import type { DfsResponse, FlowResponse, KnockoutResponse, MstResponse, UnionFindResponse } from '../types'

interface Props {
  tipo: 'uf' | 'mst' | 'dfs' | 'flow' | 'ko'
  uf?: UnionFindResponse | null
  totalNodos?: number
  mst?: MstResponse | null
  totalAristas?: number
  dfs?: DfsResponse | null
  dfsOrigen?: string
  dfsDestino?: string
  flow?: FlowResponse | null
  flowOrigen?: string
  flowDestino?: string
  ko?: KnockoutResponse | null
}

function textoUF(uf: UnionFindResponse, totalNodos?: number): string {
  const total = uf.total_componentes
  const tamanos = uf.tamanos
  const suma = totalNodos ?? tamanos.reduce((a, b) => a + b, 0)
  const max = Math.max(...tamanos)
  const idx = tamanos.indexOf(max)
  const pct = suma > 0 ? Math.round((max / suma) * 100) : 0
  return `Se formaron ${total} islas funcionales independientes con el umbral actual. El módulo dominante es la Isla ${idx + 1} con ${max} proteínas (${pct}% de la red).`
}

function textoMST(mst: MstResponse, totalAristas?: number): string {
  const redundantes = totalAristas !== undefined ? totalAristas - mst.total_aristas_mst : 0
  return `Se filtraron ${redundantes} aristas redundantes para conservar únicamente la columna vertebral de máxima confianza (${mst.total_aristas_mst} aristas, peso total ${mst.peso_total}).`
}

function textoDFS(dfs: DfsResponse, origen?: string, destino?: string): string {
  const o = origen ?? 'origen'
  const d = destino ?? 'destino'
  if (!dfs.encontrada) {
    return `No se encontró ruta: ${dfs.motivo ?? 'sin conexión disponible'} entre ${o} y ${d}.`
  }
  const intermedios = (dfs.intermedios ?? []).join(', ') || 'ninguno'
  return `Cadena de ${dfs.longitud ?? 0} saltos entre ${o} y ${d}. Intermediarios: ${intermedios}.`
}

function textoFlow(flow: FlowResponse, origen?: string, destino?: string): string {
  const o = origen ?? 'origen'
  const d = destino ?? 'destino'
  const corte = flow.corte_minimo
  const lista = corte.map((c) => `${c.source} → ${c.target}`).join(', ') || 'ninguno'
  return `Capacidad máxima de flujo de ${flow.flujo_maximo} entre ${o} y ${d}. El Corte Mínimo identifica ${corte.length} enlaces cuello de botella críticos para bloquear la vía: ${lista}.`
}

function textoKO(ko: KnockoutResponse): string {
  const { componentes_antes: antes, componentes_despues: despues } = ko.union_find
  const fragmentado = despues > antes
  const redundantes = ko.pares_semilla_desconectados.length === 0
  return `La inhibición ${fragmentado ? 'fragmentó la red' : 'no fragmentó la red'} (islas: ${antes} → ${despues}). ${ko.proteinas_aisladas.length} proteínas quedaron aisladas. ${redundantes ? 'Existen rutas alternativas redundantes que mantienen conectadas las semillas.' : 'Se detectaron pares de semilla desconectados, sin rutas alternativas directas.'}`
}

export default function InterpretacionResultado(p: Props) {
  let texto = ''
  if (p.tipo === 'uf' && p.uf) texto = textoUF(p.uf)
  else if (p.tipo === 'mst' && p.mst) texto = textoMST(p.mst, p.totalAristas)
  else if (p.tipo === 'dfs' && p.dfs) texto = textoDFS(p.dfs, p.dfsOrigen, p.dfsDestino)
  else if (p.tipo === 'flow' && p.flow) texto = textoFlow(p.flow, p.flowOrigen, p.flowDestino)
  else if (p.tipo === 'ko' && p.ko) texto = textoKO(p.ko)

  if (!texto) return null

  const icono: Record<string, string> = {
    uf: '#10b981',
    mst: '#0ea5e9',
    dfs: '#f59e0b',
    flow: '#f43f5e',
    ko: '#f43f5e',
  }

  return (
    <div className="mt-3 rounded-lg border border-[#1E293B] bg-[#111827]/60 p-3 backdrop-blur-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="w-2 h-2 rounded-full" style={{ background: icono[p.tipo] }} />
        <span className="text-xs font-bold uppercase tracking-wider text-[#94a3b8]">¿Qué significa este resultado?</span>
      </div>
      <p className="text-sm text-[#cbd5e1] leading-relaxed">{texto}</p>
    </div>
  )
}
