import { useEffect, useMemo, useRef, useState } from 'react'
import TopBar from './components/TopBar'
import LeftPanel from './components/LeftPanel'
import RightPanel from './components/RightPanel'
import GraphCanvas, { type FocusRequest, type ViewState } from './components/GraphCanvas'
import GuiaRapida from './components/GuiaRapida'
import { api, API } from './api'
import { normalizarColoresGraph, colorVia } from './theme'
import type {
  DfsResponse, FlowResponse, GraphResponse, KnockoutResponse, Mode, MstResponse, ProteinDetail, UnionFindResponse,
} from './types'

const msg = (e: unknown) => (e instanceof Error ? e.message : String(e))

export default function App() {
  // ---- filtros globales
  const [via, setVia] = useState('todas')
  const [minScoreLive, setMinScoreLive] = useState(900)
  const [minScore, setMinScore] = useState(900)
  const [maxNodos, setMaxNodos] = useState(150)

  // ---- datos
  const [graph, setGraph] = useState<GraphResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ---- selección
  const [inspected, setInspected] = useState<string | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [focus, setFocus] = useState<FocusRequest | null>(null)
  const focusN = useRef(0)
  const [detail, setDetail] = useState<ProteinDetail | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)

  // ---- algoritmos
  const [mode, setMode] = useState<Mode>('none')
  const [uf, setUf] = useState<UnionFindResponse | null>(null)
  const [ufFocus, setUfFocus] = useState<number | null>(null)
  const [mst, setMst] = useState<MstResponse | null>(null)
  const [dfs, setDfs] = useState<DfsResponse | null>(null)
  const [flow, setFlow] = useState<FlowResponse | null>(null)
  const [pathStep, setPathStep] = useState(0)
  const [origen, setOrigen] = useState('ESR1')
  const [destino, setDestino] = useState('TP53')
  const [pick, setPick] = useState<'origen' | 'destino'>('origen')
  const [minSaltos, setMinSaltos] = useState(2)
  const [evitar, setEvitar] = useState(true)
  const [busy, setBusy] = useState(false)
  const [algoError, setAlgoError] = useState<string | null>(null)
  const [guiaAbierta, setGuiaAbierta] = useState(false)

  // ---- knockout
  const [koGenes, setKoGenes] = useState<string[]>([])
  const [ko, setKo] = useState<KnockoutResponse | null>(null)
  const [koBusy, setKoBusy] = useState(false)
  const [koError, setKoError] = useState<string | null>(null)

  const filtros = useMemo(() => ({ via, minScore, maxNodos }), [via, minScore, maxNodos])

  // slider con debounce: la etiqueta es en vivo, el grafo se actualiza al soltar
  useEffect(() => {
    const t = setTimeout(() => setMinScore(minScoreLive), 350)
    return () => clearTimeout(t)
  }, [minScoreLive])

  // ---- carga del grafo
  useEffect(() => {
    let cancel = false
    setLoading(true)
    setError(null)
    api.grafo(filtros)
      .then((g) => {
        if (cancel) return
        // Normaliza los colores de los nodos a la paleta semántica del tema Bio-Slate
        const nodos = normalizarColoresGraph(g.elements.nodes.map((n) => n.data))
        setGraph({
          ...g,
          elements: { nodes: nodos.map((d) => ({ data: d })), edges: g.elements.edges },
        })
        setKoGenes([]); setKo(null); setKoError(null)
        setUf(null); setMst(null); setDfs(null); setFlow(null); setUfFocus(null); setAlgoError(null)
        const ids = new Set(g.elements.nodes.map((n) => n.data.id))
        setSelected((s) => (s && ids.has(s) ? s : null))
      })
      .catch((e) => !cancel && setError(`No se pudo cargar el grafo (${API}): ${msg(e)}`))
      .finally(() => !cancel && setLoading(false))
    return () => { cancel = true }
  }, [filtros])

  // ---- Union-Find / MST se recalculan al cambiar de modo o de filtros
  useEffect(() => {
    if (mode !== 'uf' && mode !== 'mst') return
    let cancel = false
    setBusy(true); setAlgoError(null)
    const p = mode === 'uf'
      ? api.unionFind(filtros).then((r) => !cancel && setUf(r))
      : api.mst(filtros).then((r) => !cancel && setMst(r))
    p.catch((e) => !cancel && setAlgoError(msg(e))).finally(() => !cancel && setBusy(false))
    return () => { cancel = true }
  }, [mode, filtros])

  // ---- ruta DFS iluminada paso a paso
  useEffect(() => {
    if (!dfs?.encontrada) { setPathStep(0); return }
    setPathStep(0)
    const total = dfs.nodos.length
    let i = 0
    const t = setInterval(() => {
      i += 1
      setPathStep(i)
      if (i >= total) clearInterval(t)
    }, 450)
    return () => clearInterval(t)
  }, [dfs])

  const runDfs = () => {
    setBusy(true); setAlgoError(null)
    api.dfs(filtros, origen.trim(), destino.trim(), minSaltos, evitar)
      .then(setDfs)
      .catch((e) => { setDfs(null); setAlgoError(msg(e)) })
      .finally(() => setBusy(false))
  }

  const runFlow = () => {
    setBusy(true); setAlgoError(null)
    api.flujo(filtros, origen.trim(), destino.trim())
      .then(setFlow)
      .catch((e) => { setFlow(null); setAlgoError(msg(e)) })
      .finally(() => setBusy(false))
  }

  // ---- ficha + interacciones directas
  useEffect(() => {
    if (!inspected) { setDetail(null); setDetailError(null); return }
    let cancel = false
    setDetailError(null)
    api.proteina(inspected, minScore)
      .then((d) => !cancel && setDetail({ ...d, color: colorVia(d.vias[0]) }))
      .catch((e) => { if (!cancel) { setDetail(null); setDetailError(msg(e)) } })
    return () => { cancel = true }
  }, [inspected, minScore])

  // ---- knockout (se re-simula al cambiar la lista)
  useEffect(() => {
    if (koGenes.length === 0) { setKo(null); setKoError(null); return }
    let cancel = false
    setKoBusy(true); setKoError(null)
    api.knockout(filtros, koGenes)
      .then((r) => !cancel && setKo(r))
      .catch((e) => !cancel && setKoError(msg(e)))
      .finally(() => !cancel && setKoBusy(false))
    return () => { cancel = true }
  }, [koGenes, filtros])

  // ---- helpers de selección
  const nodes = useMemo(() => graph?.elements.nodes.map((n) => n.data) ?? [], [graph])
  const nodeMap = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes])

  const requestFocus = (id: string) => setFocus({ id, n: ++focusN.current })

  const inspect = (id: string, centrar: boolean) => {
    setInspected(id)
    setSelected(nodeMap.has(id) ? id : null)
    if (centrar && nodeMap.has(id)) requestFocus(id)
  }

  const onNodeTap = (id: string) => {
    if (mode === 'dfs' || mode === 'flow') {
      if (pick === 'origen') { setOrigen(id); setPick('destino') } else { setDestino(id); setPick('origen') }
    }
    inspect(id, false)
  }

  const restaurar = () => {
    setMode('none'); setUfFocus(null); setDfs(null); setFlow(null); setAlgoError(null)
  }

  const view: ViewState = useMemo(
    () => ({ mode, uf, ufFocus, mst, dfs, flow, pathStep, koGenes, ko }),
    [mode, uf, ufFocus, mst, dfs, flow, pathStep, koGenes, ko],
  )

  return (
    <div className="flex h-full flex-col">
      <TopBar
        via={via} onVia={setVia}
        minScore={minScoreLive} onMinScore={setMinScoreLive}
        maxNodos={maxNodos} onMaxNodos={setMaxNodos}
        genes={nodes.map((n) => n.id)}
        onPick={(id) => inspect(id, true)}
        loading={loading}
        onAbrirGuia={() => setGuiaAbierta(true)}
      />
      <div className="flex min-h-0 flex-1">
        <LeftPanel
          nodes={nodes} selected={selected} onSelect={(id) => inspect(id, true)}
          koGenes={koGenes}
          mode={mode} onMode={setMode} onRestore={restaurar} busy={busy}
          totalAristas={graph?.total_aristas ?? 0}
          uf={uf} ufFocus={ufFocus} onUfFocus={setUfFocus} mst={mst} dfs={dfs} flow={flow} onRunFlow={runFlow}
          origen={origen} destino={destino} onOrigen={setOrigen} onDestino={setDestino}
          pick={pick} onPick={setPick}
          minSaltos={minSaltos} onMinSaltos={setMinSaltos}
          evitar={evitar} onEvitar={setEvitar} onRunDfs={runDfs}
          error={algoError}
        />
        <main className="relative min-w-0 flex-1">
          {graph ? (
            <GraphCanvas
              graph={graph} selected={selected} focus={focus} view={view}
              onNodeTap={onNodeTap}
              onBackgroundTap={() => { setSelected(null); setInspected(null) }}
            />
          ) : (
            <div className="canvas-bg flex h-full items-center justify-center p-8 text-center text-[#94a3b8]">
              {error ?? 'Cargando red…'}
            </div>
          )}
          {error && graph && (
            <div className="absolute left-4 top-4 rounded-md border border-[#ff1a1a] bg-[#111827] p-2 text-xs text-[#ff7a7a]">
              {error}
            </div>
          )}
        </main>
        <RightPanel
          inspected={inspected} node={inspected ? nodeMap.get(inspected) : undefined}
          detail={detail} detailError={detailError}
          colores={graph?.colores_vias ?? {}}
          koGenes={koGenes} ko={ko} koBusy={koBusy} koError={koError}
          onAddKo={(g) => setKoGenes((l) => (l.includes(g) ? l : [...l, g]))}
          onRemoveKo={(g) => setKoGenes((l) => l.filter((x) => x !== g))}
          onClearKo={() => setKoGenes([])}
          onNavigate={(g) => inspect(g, true)}
        />
      </div>
      <GuiaRapida abierta={guiaAbierta} onCerrar={() => setGuiaAbierta(false)} />
    </div>
  )
}
