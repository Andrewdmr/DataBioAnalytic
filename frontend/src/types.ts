export interface NodeData {
  id: string
  label: string
  string_id: string
  via: string
  vias: string[]
  color: string
  association_score: number
  is_seed: boolean
  degree: number
  is_hub: boolean
}

export interface EdgeData {
  id: string
  source: string
  target: string
  combined_score: number
  weight: number
}

export interface GraphResponse {
  via: string
  min_score: number
  hub: string | null
  total_nodos: number
  total_aristas: number
  colores_vias: Record<string, string>
  elements: {
    nodes: { data: NodeData }[]
    edges: { data: EdgeData }[]
  }
}

export interface UnionFindResponse {
  total_componentes: number
  componente_por_proteina: Record<string, number>
  tamanos: number[]
  componentes: string[][]
}

export interface MstResponse {
  aristas_mst: string[]
  total_aristas_mst: number
  peso_total: number
}

export interface DfsResponse {
  encontrada: boolean
  motivo?: string
  longitud?: number
  nodos: string[]
  intermedios?: string[]
  aristas: EdgeData[]
  arista_directa_ignorada?: boolean
}

export interface KnockoutResponse {
  genes: string[]
  proteinas_aisladas: string[]
  previamente_aislados: number
  proteinas_perdieron_conexion: string[]
  pares_semilla_desconectados: [string, string][]
  total_pares_desconectados: number
  total_afectadas: number
  aristas_eliminadas: number
  union_find: { componentes_antes: number; componentes_despues: number }
  mst: { peso_antes: number; peso_despues: number }
}

export interface ProteinDetail {
  symbol: string
  string_id: string
  vias: string[]
  color: string | null
  association_score: number
  total_interacciones: number
  interacciones: { symbol: string; combined_score: number }[]
}

export type Mode = 'none' | 'uf' | 'mst' | 'dfs'
