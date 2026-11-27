import type { DfsResponse, FlowResponse, Mode, MstResponse, UnionFindResponse } from '../types'

interface Props {
  mode: Mode
  uf: UnionFindResponse | null
  mst: MstResponse | null
  dfs: DfsResponse | null
  flow: FlowResponse | null
  koGenes: string[]
}

const tituloModo = (mode: Mode, koActivo: boolean): string => {
  if (koActivo) return 'Simulación Knockout'
  switch (mode) {
    case 'uf': return 'Union-Find · islas funcionales'
    case 'mst': return 'MST · columna vertebral de máxima confianza'
    case 'dfs': return 'DFS · cascada de señalización'
    case 'flow': return 'Ford-Fulkerson · flujo máximo'
    default: return 'Exploración General'
  }
}

const contenidoModo = (mode: Mode, uf: UnionFindResponse | null, mst: MstResponse | null, dfs: DfsResponse | null, flow: FlowResponse | null, koActivo: boolean): string => {
  if (koActivo) {
    return 'Simula la inhibición de genes y revela si la red se fragmenta o si existen rutas alternativas redundantes que mantienen conectadas las semillas. Selecciona genes en el Inspector biológico (derecho) para incluirlos en el knockout.'
  }
  switch (mode) {
    case 'uf': {
      const total = uf?.total_componentes ?? 0
      return `Agrupa la red en islas funcionales independientes según el umbral de confianza. Actualmente se detectan ${total} islas. Haz clic en una isla del listado para aislarla en el lienzo.`
    }
    case 'mst': {
      const totalAristas = mst?.total_aristas_mst ?? 0
      return `Conserva únicamente las aristas de máxima confianza, formando la columna vertebral de la red (${totalAristas} aristas). Las aristas desvanecidas son conexiones redundantes filtradas.`
    }
    case 'dfs':
      return 'Traza la cascada de señalización entre un gen origen y un efector destino. Haz clic en un nodo Origen y luego en un Destino del grafo para fijarlos y trazar la ruta.'
    case 'flow':
      return 'Calcula la capacidad máxima de flujo entre dos genes e identifica el Corte Mínimo (enlaces cuello de botella críticos para bloquear la vía). Fija Origen y Destino y ejecuta el cálculo.'
    default:
      return 'Explora libremente la red de proteínas. Filtra por vía y nivel de confianza, selecciona un nodo para inspeccionar sus interacciones o ejecuta algún algoritmo del panel izquierdo.'
  }
}

export default function EtapaBanner(p: Props) {
  const koActivo = p.koGenes.length > 0
  const esModoExploracion = p.mode === 'none' && !koActivo
  const titulo = koActivo || p.mode !== 'none' ? tituloModo(p.mode, koActivo) : 'Exploración General'
  const descripcion = contenidoModo(p.mode, p.uf, p.mst, p.dfs, p.flow, koActivo)

  return (
    <div className="mb-3 rounded-lg border border-[#1E293B] bg-[#111827]/80 p-3 backdrop-blur-sm text-sm">
      <div className="flex items-center gap-2 mb-1">
        <span className="w-1.5 h-1.5 rounded-full bg-[#0ea5e9]" />
        <span className="font-semibold text-[#f1f5f9] uppercase tracking-wide text-[10px]">{titulo}</span>
        {esModoExploracion && (
          <span className="ml-auto text-[10px] text-[#94a3b8]">Sin algoritmo activo · selecciona una herramienta</span>
        )}
      </div>
      <p className="text-[#cbd5e1] leading-relaxed">{descripcion}</p>
    </div>
  )
}
