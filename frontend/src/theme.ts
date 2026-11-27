// Tema científico "Bio-Slate Scientific Theme"
// Reemplaza los colores neón puros por una paleta armónica, moderna y de alto contraste.

export const THEME = {
  // Superficies y jerarquía
  fondo: '#0B1120',   // Slate 950 profundo - lienzo principal
  panel: '#111827',   // Slate 900 - paneles laterales y barra superior
  card: '#1E293B',    // Slate 800 - tarjetas internas
  cardHover: '#273549',
  borde: '#1E293B',   // Slate 800 - bordes finos
  texto: '#f1f5f9',   // Slate 100
  textoSuave: '#cbd5e1', // Slate 300
  textoMute: '#94a3b8',  // Slate 400
  acento: '#0ea5e9',  // Sky 500 - interacciones activas / selección
} as const

// Paleta semántica consistente por vía (actualizar CSS de Cytoscape.js, leyendas y badges)
export const COLOR_VIA: Record<string, string> = {
  ciclo_y_apoptosis: '#10b981',   // Esmeralda - Ciclo Celular y Apoptosis
  reparacion_adn: '#f43f5e',      // Rosa/Fucsia científico - Reparación de ADN
  senalizacion_hormonal: '#0ea5e9', // Cian/Cielo - Señalización Hormonal
  asociado: '#f59e0b',            // Ámbar cálido - Asociados Open Targets
  todas: '#94a3b8',
} as const

export const ETIQUETA_VIA: Record<string, string> = {
  ciclo_y_apoptosis: 'Ciclo Celular y Apoptosis',
  senalizacion_hormonal: 'Señalización Hormonal',
  reparacion_adn: 'Reparación de ADN',
  asociado: 'Asociado (Open Targets)',
  todas: 'Todas las vías',
} as const

// Aristas normales: gris azulado translúcido para reducir ruido visual
export const COLOR_ARISTA_NORMAL = 'rgba(148, 163, 184, 0.6)'

export const LEGEND_ENTRIES: { via: string; label: string }[] = [
  { via: 'ciclo_y_apoptosis', label: 'Ciclo Celular y Apoptosis' },
  { via: 'reparacion_adn', label: 'Reparación de ADN' },
  { via: 'senalizacion_hormonal', label: 'Señalización Hormonal' },
  { via: 'asociado', label: 'Asociados Open Targets' },
]

/** Devuelve el color semántico de una vía (fallback gris para vías desconocidas). */
export function colorVia(via: string | undefined): string {
  return COLOR_VIA[via ?? 'todas'] ?? COLOR_VIA.todas
}

/** Colores por componente (islas Union-Find) — cicla sobre la paleta semántica del tema. */
export const colorComponente = (i: number) => {
  const colores = ['#10b981', '#0ea5e9', '#f59e0b', '#f43f5e', '#94a3b8', '#22d3ee']
  return colores[i % colores.length]
}

/** Normaliza el color de los nodos del grafo según la paleta semántica del tema. */
export function normalizarColoresGraph<V extends { via?: string; color?: string }>(
  elementos: V[],
): V[] {
  return elementos.map((e) => ({ ...e, color: colorVia(e.via) }))
}
