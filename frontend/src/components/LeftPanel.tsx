import { useEffect, useMemo, useRef, useState } from 'react'
import { Info, Network, Play, RotateCcw, Route, Share2, TreePine, Waves } from 'lucide-react'
import type { DfsResponse, FlowResponse, Mode, MstResponse, NodeData, UnionFindResponse } from '../types'
import { colorComponente } from '../theme'
import EtapaBanner from './EtapaBanner'
import InterpretacionResultado from './InterpretacionResultado'

interface Props {
  nodes: NodeData[]
  selected: string | null
  onSelect: (id: string) => void
  koGenes: string[]
  mode: Mode
  onMode: (m: Mode) => void
  onRestore: () => void
  busy: boolean
  totalAristas?: number
  uf: UnionFindResponse | null
  ufFocus: number | null
  onUfFocus: (i: number | null) => void
  mst: MstResponse | null
  dfs: DfsResponse | null
  flow: FlowResponse | null
  onRunFlow: () => void
  origen: string
  destino: string
  onOrigen: (s: string) => void
  onDestino: (s: string) => void
  pick: 'origen' | 'destino'
  onPick: (p: 'origen' | 'destino') => void
  minSaltos: number
  onMinSaltos: (n: number) => void
  evitar: boolean
  onEvitar: (b: boolean) => void
  onRunDfs: () => void
  error: string | null
}

export default function LeftPanel(p: Props) {
  const [filtro, setFiltro] = useState('')
  const itemRefs = useRef<Record<string, HTMLLIElement | null>>({})

  const lista = useMemo(() => {
    const t = filtro.trim().toUpperCase()
    return [...p.nodes]
      .filter((n) => !t || n.id.includes(t))
      .sort((a, b) => b.association_score - a.association_score)
  }, [p.nodes, filtro])

  useEffect(() => {
    if (p.selected) itemRefs.current[p.selected]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }, [p.selected])

  const modoBtn = (m: Mode, icon: React.ReactNode, label: string) => (
    <button
      onClick={() => p.onMode(p.mode === m ? 'none' : m)}
      className={`flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm transition ${
        p.mode === m
          ? 'border-[#0ea5e9] bg-[#273549] text-[#0ea5e9]'
          : 'border-[#1E293B] text-[#cbd5e1] hover:border-[#94a3b8] hover:bg-[#273549]'}`}
    >
      {icon} {label}
    </button>
  )

  const help = (label: string) => (
    <span className="help-icon" title={label}>
      <Info size={13} className="text-[#94a3b8]" />
    </span>
  )

  const ids = p.nodes.map((n) => n.id)
  const idSel = (value: string, onChange: (s: string) => void, active: boolean, which: 'origen' | 'destino') => (
    <div className="flex items-center gap-1">
      <button onClick={() => p.onPick(which)} title="Click en el grafo para asignar"
              className={`w-16 rounded px-1 py-1 text-xs ${active ? 'bg-[#f59e0b] text-black' : 'bg-[#1E293B] border border-[#1E293B]'}`}>
        {which === 'origen' ? 'Origen' : 'Destino'}
      </button>
      <input type="text" list="genes-dfs" value={value}
             onChange={(e) => onChange(e.target.value.toUpperCase())} className="min-w-0 flex-1 !py-1" />
    </div>
  )

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-[#1E293B] bg-[#111827]">
      <div className="space-y-2 border-b border-[#1E293B] p-3">
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-[#94a3b8]">
          Algoritmos
          <button onClick={p.onRestore} className="flex items-center gap-1 normal-case text-[#f59e0b] hover:underline">
            <RotateCcw size={12} /> Restaurar vista
          </button>
        </div>

        {/* Banner de contexto de etapa */}
        <EtapaBanner
          mode={p.mode} uf={p.uf} mst={p.mst} dfs={p.dfs} flow={p.flow} koGenes={p.koGenes}
        />

        {modoBtn('uf', <Network size={15} />, 'Union-Find · islas funcionales')}
        {p.mode === 'uf' && p.uf && (
          <div className="rounded-md border border-[#1E293B] bg-[#1E293B] p-2 text-xs">
            <div className="mb-1 text-2xl font-bold text-[#10b981]">
              {p.uf.total_componentes} <span className="text-xs font-normal text-[#94a3b8]">islas detectadas</span>
            </div>
            <ul className="max-h-28 space-y-0.5 overflow-y-auto">
              {p.uf.tamanos.map((t, i) => (
                <li key={i} onClick={() => p.onUfFocus(p.ufFocus === i ? null : i)}
                    className={`flex cursor-pointer items-center gap-2 rounded px-1 hover:bg-[#0a2a4a] ${p.ufFocus === i ? 'bg-[#0a2a4a]' : ''}`}>
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: colorComponente(i) }} />
                  Isla {i + 1}: {t} {t === 1 ? 'nodo' : 'nodos'}
                </li>
              ))}
            </ul>
            <InterpretacionResultado
              tipo="uf"
              uf={p.uf}
              totalNodos={p.nodes.length}
            />
          </div>
        )}

        {modoBtn('mst', <TreePine size={15} />, 'MST · vista esqueleto')}
        {p.mode === 'mst' && p.mst && (
          <div className="rounded-md border border-[#1E293B] bg-[#1E293B] p-2 text-xs text-[#cbd5e1]">
            <b className="text-[#f1f5f9]">{p.mst.total_aristas_mst}</b> aristas en el árbol · peso total{' '}
            <b className="text-[#f1f5f9]">{p.mst.peso_total}</b>
            <div className="text-[#94a3b8]">peso = 1000 − combined_score</div>
            <InterpretacionResultado
              tipo="mst"
              mst={p.mst}
              totalAristas={p.totalAristas}
            />
          </div>
        )}

        {modoBtn('dfs', <Route size={15} />, 'DFS · ruta de señalización')}
        {p.mode === 'dfs' && (
          <div className="space-y-2 rounded-md border border-[#1E293B] bg-[#1E293B] p-2 text-xs">
            <datalist id="genes-dfs">{ids.map((g) => <option key={g} value={g} />)}</datalist>
            {idSel(p.origen, p.onOrigen, p.pick === 'origen', 'origen')}
            {idSel(p.destino, p.onDestino, p.pick === 'destino', 'destino')}
            <div className="text-[#94a3b8]">Haz clic en nodos del grafo para fijar el {p.pick}.</div>
            <label className="flex items-center gap-2">min_saltos
              {help('Cantidad mínima de nodos intermedios que debe tener la ruta entre el origen y el destino.')}
              <input type="number" min={1} max={9} value={p.minSaltos}
                     onChange={(e) => p.onMinSaltos(Number(e.target.value) || 1)} className="w-14 !py-0.5" />
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={p.evitar} onChange={(e) => p.onEvitar(e.target.checked)} />
              Evitar enlace directo
              {help('Descarta la arista directa entre origen y destino para forzar rutas a través de intermediarios.')}
            </label>
            <button onClick={p.onRunDfs} disabled={!p.origen || !p.destino || p.busy}
                    className="flex w-full items-center justify-center gap-1 rounded bg-[#0ea5e9] py-1.5 font-semibold text-white disabled:opacity-40 hover:bg-[#0891b2]">
              <Play size={12} /> Trazar ruta
            </button>
            {p.dfs && (
              <div className="rounded border border-[#1E293B] p-2">
                {p.dfs.encontrada ? (
                  <>
                    <div className="mb-1 flex items-center gap-1 text-[#94a3b8]"><Share2 size={12} /> {p.dfs.longitud} saltos
                      {p.dfs.arista_directa_ignorada && ' · enlace directo ignorado'}</div>
                    <div className="font-mono text-[#f59e0b]">{p.dfs.nodos.join(' → ')}</div>
                  </>
                ) : (
                  <span className="text-[#f43f5e]">{p.dfs.motivo ?? 'Sin ruta'}</span>
                )}
                <InterpretacionResultado
                  tipo="dfs"
                  dfs={p.dfs}
                  dfsOrigen={p.origen}
                  dfsDestino={p.destino}
                />
              </div>
            )}
          </div>
        )}
        {modoBtn('flow', <Waves size={15} />, 'Ford-Fulkerson · flujo máximo')}
        {p.mode === 'flow' && (
          <div className="space-y-2 rounded-md border border-[#1E293B] bg-[#1E293B] p-2 text-xs">
            <datalist id="genes-dfs">{ids.map((g) => <option key={g} value={g} />)}</datalist>
            {idSel(p.origen, p.onOrigen, p.pick === 'origen', 'origen')}
            {idSel(p.destino, p.onDestino, p.pick === 'destino', 'destino')}
            <div className="text-[#94a3b8]">Fuente = origen · Sumidero = destino. Clic en el grafo para fijar el {p.pick}.</div>
            <button onClick={p.onRunFlow} disabled={!p.origen || !p.destino || p.busy}
                    className="flex w-full items-center justify-center gap-1 rounded bg-[#0ea5e9] py-1.5 font-semibold text-white disabled:opacity-40 hover:bg-[#0891b2]">
              <Play size={12} /> Calcular flujo máximo
            </button>
            {p.flow && (
              <div className="space-y-1 rounded border border-[#1E293B] p-2">
                <div className="text-2xl font-bold text-[#0ea5e9]">
                  {p.flow.flujo_maximo} <span className="text-xs font-normal text-[#94a3b8]">flujo máximo</span>
                </div>
                <div className="text-[#cbd5e1]">{p.flow.caminos_aumento} caminos de aumento · {p.flow.aristas_flujo.length} aristas con flujo</div>
                <div className="text-[#f43f5e]">Corte mínimo ({p.flow.corte_minimo.length} aristas críticas):</div>
                <ul className="max-h-28 overflow-y-auto font-mono text-[#cbd5e1]">
                  {p.flow.corte_minimo.map((c) => (
                    <li key={c.id}>{c.source} — {c.target} <span className="text-[#94a3b8]">({c.capacidad})</span></li>
                  ))}
                  {p.flow.corte_minimo.length === 0 && <li className="text-[#94a3b8]">sin conexión: flujo 0</li>}
                </ul>
                <InterpretacionResultado
                  tipo="flow"
                  flow={p.flow}
                  flowOrigen={p.origen}
                  flowDestino={p.destino}
                />
              </div>
            )}
          </div>
        )}
        {p.error && <div className="rounded border border-[#ff1a1a] p-2 text-xs text-[#ff7a7a]">{p.error}</div>}
      </div>

      <div className="flex min-h-0 flex-1 flex-col bg-[#111827]">
        <div className="p-3 pb-1">
          <input type="search" placeholder={`Filtrar ${p.nodes.length} proteínas…`} value={filtro}
                 onChange={(e) => setFiltro(e.target.value)} className="w-full" />
        </div>
        <ul className="min-h-0 flex-1 overflow-y-auto pb-3">
          {lista.map((n) => {
            const activo = n.id === p.selected
            const ko = p.koGenes.includes(n.id)
            return (
              <li key={n.id} ref={(el) => { itemRefs.current[n.id] = el }} onClick={() => p.onSelect(n.id)}
                  className="flex cursor-pointer items-center gap-2 px-4 py-1.5 text-sm hover:bg-[#273549]"
                  style={{ color: activo ? n.color : undefined, fontWeight: activo ? 700 : 400 }}>
                <span className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ background: n.color, opacity: activo ? 1 : 0.55 }} />
                <span className={ko ? 'text-[#f43f5e] line-through' : ''}>{n.id}</span>
                <span className="ml-auto font-mono text-[10px] text-[#94a3b8]">{n.association_score.toFixed(2)}</span>
              </li>
            )
          })}
        </ul>
      </div>
    </aside>
  )
}
