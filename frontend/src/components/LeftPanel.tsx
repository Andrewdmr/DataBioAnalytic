import { useEffect, useMemo, useRef, useState } from 'react'
import { Network, Play, RotateCcw, Route, Share2, TreePine, Waves } from 'lucide-react'
import type { DfsResponse, FlowResponse, Mode, MstResponse, NodeData, UnionFindResponse } from '../types'
import { colorComponente } from './GraphCanvas'

interface Props {
  nodes: NodeData[]
  selected: string | null
  onSelect: (id: string) => void
  koGenes: string[]
  mode: Mode
  onMode: (m: Mode) => void
  onRestore: () => void
  busy: boolean
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
        p.mode === m ? 'border-[#00e5ff] bg-[#0a2a4a] text-[#00e5ff]' : 'panel-borde hover:border-slate-400'}`}
    >
      {icon} {label}
    </button>
  )

  const ids = p.nodes.map((n) => n.id)
  const idSel = (value: string, onChange: (s: string) => void, active: boolean, which: 'origen' | 'destino') => (
    <div className="flex items-center gap-1">
      <button onClick={() => p.onPick(which)} title="Click en el grafo para asignar"
              className={`w-16 rounded px-1 py-1 text-xs ${active ? 'bg-[#ffee00] text-black' : 'bg-[#02101f] border panel-borde'}`}>
        {which === 'origen' ? 'Origen' : 'Destino'}
      </button>
      <input type="text" list="genes-dfs" value={value}
             onChange={(e) => onChange(e.target.value.toUpperCase())} className="min-w-0 flex-1 !py-1" />
    </div>
  )

  return (
    <aside className="flex w-72 shrink-0 flex-col border-r-2 border-white">
      <div className="space-y-2 border-b panel-borde p-3">
        <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-400">
          Algoritmos
          <button onClick={p.onRestore} className="flex items-center gap-1 normal-case text-[#ffbb00] hover:underline">
            <RotateCcw size={12} /> Restaurar vista
          </button>
        </div>

        {modoBtn('uf', <Network size={15} />, 'Union-Find · islas funcionales')}
        {p.mode === 'uf' && p.uf && (
          <div className="rounded-md border panel-borde bg-[#02101f] p-2 text-xs">
            <div className="mb-1 text-2xl font-bold text-[#aaff00]">
              {p.uf.total_componentes} <span className="text-xs font-normal text-slate-400">islas detectadas</span>
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
          </div>
        )}

        {modoBtn('mst', <TreePine size={15} />, 'MST · vista esqueleto')}
        {p.mode === 'mst' && p.mst && (
          <div className="rounded-md border panel-borde bg-[#02101f] p-2 text-xs text-slate-300">
            <b className="text-white">{p.mst.total_aristas_mst}</b> aristas en el árbol · peso total{' '}
            <b className="text-white">{p.mst.peso_total}</b>
            <div className="text-slate-500">peso = 1000 − combined_score</div>
          </div>
        )}

        {modoBtn('dfs', <Route size={15} />, 'DFS · ruta de señalización')}
        {p.mode === 'dfs' && (
          <div className="space-y-2 rounded-md border panel-borde bg-[#02101f] p-2 text-xs">
            <datalist id="genes-dfs">{ids.map((g) => <option key={g} value={g} />)}</datalist>
            {idSel(p.origen, p.onOrigen, p.pick === 'origen', 'origen')}
            {idSel(p.destino, p.onDestino, p.pick === 'destino', 'destino')}
            <div className="text-slate-500">Haz clic en nodos del grafo para fijar el {p.pick}.</div>
            <label className="flex items-center gap-2">min_saltos
              <input type="number" min={1} max={9} value={p.minSaltos}
                     onChange={(e) => p.onMinSaltos(Number(e.target.value) || 1)} className="w-14 !py-0.5" />
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={p.evitar} onChange={(e) => p.onEvitar(e.target.checked)} />
              Evitar enlace directo
            </label>
            <button onClick={p.onRunDfs} disabled={!p.origen || !p.destino || p.busy}
                    className="flex w-full items-center justify-center gap-1 rounded bg-[#ffee00] py-1.5 font-semibold text-black disabled:opacity-40">
              <Play size={12} /> Trazar ruta
            </button>
            {p.dfs && (
              <div className="rounded border panel-borde p-2">
                {p.dfs.encontrada ? (
                  <>
                    <div className="mb-1 flex items-center gap-1 text-slate-400"><Share2 size={12} /> {p.dfs.longitud} saltos
                      {p.dfs.arista_directa_ignorada && ' · enlace directo ignorado'}</div>
                    <div className="font-mono text-[#ffee00]">{p.dfs.nodos.join(' → ')}</div>
                  </>
                ) : (
                  <span className="text-[#ff5a5a]">{p.dfs.motivo ?? 'Sin ruta'}</span>
                )}
              </div>
            )}
          </div>
        )}
        {modoBtn('flow', <Waves size={15} />, 'Ford-Fulkerson · flujo máximo')}
        {p.mode === 'flow' && (
          <div className="space-y-2 rounded-md border panel-borde bg-[#02101f] p-2 text-xs">
            <datalist id="genes-dfs">{ids.map((g) => <option key={g} value={g} />)}</datalist>
            {idSel(p.origen, p.onOrigen, p.pick === 'origen', 'origen')}
            {idSel(p.destino, p.onDestino, p.pick === 'destino', 'destino')}
            <div className="text-slate-500">Fuente = origen · Sumidero = destino. Clic en el grafo para fijar el {p.pick}.</div>
            <button onClick={p.onRunFlow} disabled={!p.origen || !p.destino || p.busy}
                    className="flex w-full items-center justify-center gap-1 rounded bg-[#00b7ff] py-1.5 font-semibold text-black disabled:opacity-40">
              <Play size={12} /> Calcular flujo máximo
            </button>
            {p.flow && (
              <div className="space-y-1 rounded border panel-borde p-2">
                <div className="text-2xl font-bold text-[#00b7ff]">
                  {p.flow.flujo_maximo} <span className="text-xs font-normal text-slate-400">flujo máximo</span>
                </div>
                <div className="text-slate-300">{p.flow.caminos_aumento} caminos de aumento · {p.flow.aristas_flujo.length} aristas con flujo</div>
                <div className="text-[#ff5a5a]">Corte mínimo ({p.flow.corte_minimo.length} aristas críticas):</div>
                <ul className="max-h-28 overflow-y-auto font-mono text-slate-200">
                  {p.flow.corte_minimo.map((c) => (
                    <li key={c.id}>{c.source} — {c.target} <span className="text-slate-500">({c.capacidad})</span></li>
                  ))}
                  {p.flow.corte_minimo.length === 0 && <li className="text-slate-500">sin conexión: flujo 0</li>}
                </ul>
              </div>
            )}
          </div>
        )}
        {p.error && <div className="rounded border border-[#ff1a1a] p-2 text-xs text-[#ff7a7a]">{p.error}</div>}
      </div>

      <div className="flex min-h-0 flex-1 flex-col">
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
                  className="flex cursor-pointer items-center gap-2 px-4 py-1.5 text-sm hover:bg-[#0a2a4a]"
                  style={{ color: activo ? n.color : undefined, fontWeight: activo ? 700 : 400 }}>
                <span className="h-2.5 w-2.5 shrink-0 rounded-full"
                      style={{ background: n.color, opacity: activo ? 1 : 0.55 }} />
                <span className={ko ? 'text-[#ff5a5a] line-through' : ''}>{n.id}</span>
                <span className="ml-auto font-mono text-[10px] text-slate-500">{n.association_score.toFixed(2)}</span>
              </li>
            )
          })}
        </ul>
      </div>
    </aside>
  )
}
