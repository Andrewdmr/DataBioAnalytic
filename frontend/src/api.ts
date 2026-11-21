import type {
  DfsResponse, FlowResponse, GraphResponse, KnockoutResponse, MstResponse, ProteinDetail, UnionFindResponse,
} from './types'

export const API = (import.meta.env.VITE_API as string | undefined) ?? 'http://localhost:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, init)
  if (!res.ok) {
    let detalle = res.statusText
    try { detalle = (await res.json()).detail ?? detalle } catch { /* sin cuerpo */ }
    throw new Error(typeof detalle === 'string' ? detalle : JSON.stringify(detalle))
  }
  return res.json() as Promise<T>
}

interface Filtros { via: string; minScore: number; maxNodos: number }
const qs = (f: Filtros) => `via=${f.via}&min_score=${f.minScore}&max_nodos=${f.maxNodos}`

export const api = {
  grafo: (f: Filtros) => request<GraphResponse>(`/grafo?${qs(f)}`),
  unionFind: (f: Filtros) => request<UnionFindResponse>(`/algoritmos/union-find?${qs(f)}`),
  mst: (f: Filtros) => request<MstResponse>(`/algoritmos/mst?${qs(f)}`),
  dfs: (f: Filtros, origen: string, destino: string, minSaltos: number, evitarDirecto: boolean) =>
    request<DfsResponse>(
      `/algoritmos/dfs?${qs(f)}&origen=${origen}&destino=${destino}` +
      `&min_saltos=${minSaltos}&evitar_directo=${evitarDirecto}`),
  flujo: (f: Filtros, origen: string, destino: string) =>
    request<FlowResponse>(`/algoritmos/flujo-maximo?${qs(f)}&origen=${origen}&destino=${destino}`),
  knockout: (f: Filtros, genes: string[]) =>
    request<KnockoutResponse>('/simulacion/knockout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ genes, via: f.via, min_score: f.minScore, max_nodos: f.maxNodos }),
    }),
  proteina: (symbol: string, minScore: number) =>
    request<ProteinDetail>(`/proteina/${encodeURIComponent(symbol)}?min_score=${minScore}`),
}
