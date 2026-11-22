import { FlaskConical, Plus, Trash2, X } from 'lucide-react'
import type { KnockoutResponse, NodeData, ProteinDetail } from '../types'

interface Props {
  inspected: string | null
  node: NodeData | undefined
  detail: ProteinDetail | null
  detailError: string | null
  colores: Record<string, string>
  koGenes: string[]
  ko: KnockoutResponse | null
  koBusy: boolean
  onAddKo: (g: string) => void
  onRemoveKo: (g: string) => void
  onClearKo: () => void
  onNavigate: (g: string) => void
  koError: string | null
}

const ETIQUETA_VIA: Record<string, string> = {
  ciclo_y_apoptosis: 'Ciclo Celular y Apoptosis',
  senalizacion_hormonal: 'Señalización Hormonal',
  reparacion_adn: 'Reparación de ADN',
  asociado: 'Asociado (Open Targets)',
}

export default function RightPanel(p: Props) {
  const color = p.node?.color ?? p.detail?.color ?? '#ffbb00'
  const via = p.node?.via ?? p.detail?.vias[0] ?? 'asociado'
  const yaKo = !!p.inspected && p.koGenes.includes(p.inspected)

  return (
    <aside className="flex w-80 shrink-0 flex-col overflow-y-auto border-l-2 border-white">
      <section className="border-b panel-borde p-4">
        <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Inspector biológico</div>
        {!p.inspected ? (
          <p className="text-sm text-slate-500">Haz clic en un nodo del grafo para ver su ficha.</p>
        ) : (
          <>
            <div className="mb-3 flex items-center gap-2">
              <span className="h-3.5 w-3.5 rounded-full" style={{ background: color, boxShadow: `0 0 10px ${color}` }} />
              <h2 className="text-xl font-bold" style={{ color }}>{p.inspected}</h2>
            </div>
            <dl className="grid grid-cols-2 gap-y-1 text-sm">
              <dt className="text-slate-400">Vía</dt>
              <dd>{ETIQUETA_VIA[via] ?? via}</dd>
              <dt className="text-slate-400">association_score</dt>
              <dd className="font-mono">{(p.node?.association_score ?? p.detail?.association_score ?? 0).toFixed(3)}</dd>
              <dt className="text-slate-400">Grado actual</dt>
              <dd className="font-mono">{p.node ? p.node.degree : '—'}{p.node?.is_hub && ' · HUB'}</dd>
              <dt className="text-slate-400">Semilla</dt>
              <dd>{p.node ? (p.node.is_seed ? 'sí' : 'no') : '—'}</dd>
            </dl>
            {!p.node && (
              <p className="mt-2 text-xs text-[#ffbb00]">Esta proteína no está en el subgrafo actual.</p>
            )}
          </>
        )}
      </section>

      <section className="border-b panel-borde p-4">
        <div className="mb-2 flex items-center gap-1 text-xs uppercase tracking-wide text-slate-400">
          <FlaskConical size={13} /> Simulador knockout
        </div>
        <button
          disabled={!p.inspected || !p.node || yaKo || p.koBusy}
          onClick={() => p.inspected && p.onAddKo(p.inspected)}
          className="flex w-full items-center justify-center gap-1 rounded-md bg-[#ff1a1a] py-2 text-sm font-semibold text-white disabled:opacity-40"
        >
          <Plus size={14} /> Agregar a Knockout / Inhibir Gen
        </button>

        {p.koGenes.length > 0 && (
          <>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {p.koGenes.map((g) => (
                <span key={g} className="flex items-center gap-1 rounded-full border border-[#ff1a1a] px-2 py-0.5 text-xs text-[#ff7a7a]">
                  <span className="line-through">{g}</span>
                  <X size={12} className="cursor-pointer" onClick={() => p.onRemoveKo(g)} />
                </span>
              ))}
            </div>
            <button onClick={p.onClearKo}
                    className="mt-2 flex w-full items-center justify-center gap-1 rounded-md border panel-borde py-1.5 text-xs hover:border-slate-300">
              <Trash2 size={12} /> Limpiar Knockout
            </button>
          </>
        )}
        {p.koBusy && <div className="mt-2 text-xs text-[#ffbb00]">simulando…</div>}
        {p.koError && <div className="mt-2 text-xs text-[#ff7a7a]">{p.koError}</div>}

        {p.ko && (
          <div className="mt-3 space-y-2 rounded-md border panel-borde bg-[#02101f] p-2 text-xs">
            <div>Islas: <b>{p.ko.union_find.componentes_antes}</b> → <b className="text-[#ffbb00]">{p.ko.union_find.componentes_despues}</b>
              {' '}· aristas eliminadas: <b>{p.ko.aristas_eliminadas}</b></div>
            <div>
              <span className="text-[#ff7a7a]">Proteínas aisladas ({p.ko.proteinas_aisladas.length}):</span>{' '}
              {p.ko.proteinas_aisladas.length ? p.ko.proteinas_aisladas.join(', ') : 'ninguna'}
            </div>
            {p.ko.proteinas_perdieron_conexion.length > 0 && (
              <div>
                <span className="text-[#ffbb00]">Perdieron conexión ({p.ko.proteinas_perdieron_conexion.length}):</span>{' '}
                {p.ko.proteinas_perdieron_conexion.join(', ')}
              </div>
            )}
            <div>
              <span className="text-[#ffbb00]">Pares semilla desconectados ({p.ko.total_pares_desconectados}):</span>
              {p.ko.pares_semilla_desconectados.length === 0 ? ' ninguno' : (
                <ul className="mt-0.5 max-h-24 overflow-y-auto font-mono">
                  {p.ko.pares_semilla_desconectados.map(([a, b]) => <li key={a + b}>{a} ⇎ {b}</li>)}
                </ul>
              )}
            </div>
            {p.ko.previamente_aislados > 0 && (
              <div className="text-slate-500">{p.ko.previamente_aislados} proteínas ya estaban aisladas antes del knockout.</div>
            )}
          </div>
        )}
      </section>

      <section className="p-4">
        <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">
          Interacciones directas {p.detail && `(${p.detail.interacciones.length})`}
        </div>
        {p.detailError && <div className="text-xs text-[#ff7a7a]">{p.detailError}</div>}
        {p.detail && (
          <ul className="space-y-0.5">
            {p.detail.interacciones.map((i) => (
              <li key={i.symbol} onClick={() => p.onNavigate(i.symbol)}
                  className="flex cursor-pointer items-center justify-between rounded px-2 py-1 text-sm hover:bg-[#0a2a4a]">
                <span>{i.symbol}</span>
                <span className="flex items-center gap-2">
                  <span className="h-1.5 rounded bg-[#00e5ff]" style={{ width: `${(i.combined_score / 1000) * 40}px` }} />
                  <span className="font-mono text-xs text-slate-400">{i.combined_score}</span>
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </aside>
  )
}
