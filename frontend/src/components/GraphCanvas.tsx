import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import type cytoscape from 'cytoscape'
import { Download, LocateFixed, Minus, Plus } from 'lucide-react'
import type { DfsResponse, FlowResponse, GraphResponse, KnockoutResponse, Mode, MstResponse, UnionFindResponse } from '../types'

export interface ViewState {
  mode: Mode
  uf: UnionFindResponse | null
  ufFocus: number | null
  mst: MstResponse | null
  dfs: DfsResponse | null
  flow: FlowResponse | null
  pathStep: number
  koGenes: string[]
  ko: KnockoutResponse | null
}

export interface FocusRequest { id: string; n: number }

interface Props {
  graph: GraphResponse
  selected: string | null
  focus: FocusRequest | null
  view: ViewState
  onNodeTap: (id: string) => void
  onBackgroundTap: () => void
}

const XSVG =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><path d="M6 6L34 34M34 6L6 34" stroke="#ff1a1a" stroke-width="6" stroke-linecap="round"/></svg>',
  )

const STYLESHEET: cytoscape.StylesheetJson = [
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      width: 'mapData(association_score, 0, 1, 18, 46)',
      height: 'mapData(association_score, 0, 1, 18, 46)',
      label: 'data(label)',
      color: '#dfe8f5',
      'font-size': 9,
      'text-valign': 'bottom',
      'text-margin-y': 3,
      'text-outline-color': '#000814',
      'text-outline-width': 2,
      'min-zoomed-font-size': 7,
      'border-width': 0,
      'transition-property': 'opacity, background-color',
      'transition-duration': 200,
    },
  },
  {
    // Hub: anillo exterior punteado (como en app2.py)
    selector: 'node[?is_hub]',
    style: {
      'border-width': 3,
      'border-style': 'dashed',
      'border-color': 'data(color)',
      'border-opacity': 1,
      'font-weight': 'bold',
    },
  },
  {
    selector: 'node:selected',
    style: { 'border-width': 3, 'border-style': 'solid', 'border-color': '#ffffff', 'font-weight': 'bold' },
  },
  {
    selector: 'edge',
    style: {
      width: 'mapData(combined_score, 400, 1000, 0.8, 4)',
      'line-color': '#ffffff',
      opacity: 'mapData(combined_score, 400, 1000, 0.18, 0.8)' as unknown as number,
      'curve-style': 'haystack',
    },
  },
  { selector: 'node.faded', style: { opacity: 0.12 } },
  { selector: 'edge.faded, edge.edgefaded', style: { opacity: 0.1 } },
  { selector: 'edge.mst', style: { width: 4.5, 'line-color': '#ffffff', opacity: 1, 'curve-style': 'bezier' } },
  { selector: 'edge.flow', style: { 'line-color': '#00b7ff', opacity: 1, 'curve-style': 'bezier', 'z-index': 50 } },
  {
    selector: 'edge.cut',
    style: {
      width: 5, 'line-color': '#ff1a1a', 'line-style': 'dashed', 'line-dash-pattern': [6, 4],
      opacity: 1, 'curve-style': 'bezier', 'z-index': 100,
    },
  },
  { selector: 'edge.path', style: { width: 6, 'line-color': '#ffee00', opacity: 1, 'curve-style': 'bezier', 'z-index': 99 } },
  { selector: 'node.path', style: { 'border-width': 4, 'border-style': 'solid', 'border-color': '#ffee00', opacity: 1, 'z-index': 99 } },
  {
    selector: 'node.ko',
    style: {
      opacity: 0.45,
      'background-image': XSVG,
      'background-fit': 'contain',
      'background-clip': 'none',
      'border-width': 2,
      'border-style': 'solid',
      'border-color': '#ff1a1a',
      color: '#ff5a5a',
    },
  },
  {
    selector: 'node.isolated',
    style: {
      'underlay-color': '#ff1a1a', 'underlay-opacity': 0.55, 'underlay-padding': 9, 'underlay-shape': 'ellipse',
    },
  },
  {
    selector: 'node.pair',
    style: {
      'underlay-color': '#ffbb00', 'underlay-opacity': 0.5, 'underlay-padding': 9, 'underlay-shape': 'ellipse',
    },
  },
]

/** Color distinto por componente (ángulo áureo en HSL, estilo neón). */
export const colorComponente = (i: number) => `hsl(${(i * 137.508) % 360}, 100%, 60%)`

export default function GraphCanvas({ graph, selected, focus, view, onNodeTap, onBackgroundTap }: Props) {
  const cyRef = useRef<cytoscape.Core | null>(null)
  const boundRef = useRef<cytoscape.Core | null>(null)
  const tapRef = useRef({ onNodeTap, onBackgroundTap })
  tapRef.current = { onNodeTap, onBackgroundTap }
  const [tip, setTip] = useState<{ x: number; y: number; id: string; score: number } | null>(null)

  const elements = useMemo(
    () => [
      ...graph.elements.nodes.map((n) => ({ data: n.data, group: 'nodes' as const })),
      ...graph.elements.edges.map((e) => ({ data: e.data, group: 'edges' as const })),
    ],
    [graph],
  )

  const recentrar = useCallback(() => {
    cyRef.current?.animate({ fit: { eles: cyRef.current.elements(), padding: 40 }, duration: 400 })
  }, [])

  const onCy = useCallback((cy: cytoscape.Core) => {
    cyRef.current = cy
    if (boundRef.current === cy) return
    boundRef.current = cy
    cy.on('tap', 'node', (e) => tapRef.current.onNodeTap(e.target.id()))
    cy.on('tap', (e) => { if (e.target === cy) tapRef.current.onBackgroundTap() })
    cy.on('mouseover', 'node', (e) => {
      const p = e.target.renderedPosition()
      setTip({ x: p.x, y: p.y, id: e.target.id(), score: e.target.data('association_score') })
    })
    cy.on('mouseout', 'node', () => setTip(null))
    cy.on('drag pan zoom', () => setTip(null))
  }, [])

  // Layout force-directed (cose) cada vez que cambia el grafo
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.layout({
      name: 'cose', animate: false, randomize: true, fit: true, padding: 40,
      nodeRepulsion: () => 12000, idealEdgeLength: () => 70, edgeElasticity: () => 80,
      gravity: 0.6, componentSpacing: 80, numIter: 1200,
    } as cytoscape.LayoutOptions).run()
  }, [graph])

  // Selección sincronizada con la lista / buscador
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.nodes().unselect()
    if (selected) cy.getElementById(selected).select()
  }, [selected, graph])

  // Zoom suave al nodo solicitado
  useEffect(() => {
    const cy = cyRef.current
    if (!cy || !focus) return
    const n = cy.getElementById(focus.id)
    if (n.nonempty()) cy.animate({ center: { eles: n }, zoom: Math.max(cy.zoom(), 1.6) }, { duration: 500 })
  }, [focus])

  // Aplicación de vistas de algoritmos + knockout
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    cy.batch(() => {
      cy.elements().removeClass('faded edgefaded mst path ko isolated pair')
      cy.elements().removeStyle()

      if (view.mode === 'uf' && view.uf) {
        const comp = view.uf.componente_por_proteina
        cy.nodes().forEach((n) => {
          const c = comp[n.id()]
          if (c === undefined) return
          n.style('background-color', colorComponente(c))
          if (view.ufFocus !== null && c !== view.ufFocus) n.addClass('faded')
        })
        if (view.ufFocus !== null) {
          cy.edges().forEach((e) => {
            if (comp[e.source().id()] !== view.ufFocus) e.addClass('faded')
          })
        }
      }

      if (view.mode === 'mst' && view.mst) {
        const ids = new Set(view.mst.aristas_mst)
        cy.edges().forEach((e) => { e.addClass(ids.has(e.id()) ? 'mst' : 'edgefaded') })
      }

      if (view.mode === 'flow' && view.flow) {
        const flujo = new Map(view.flow.aristas_flujo.map((a) => [a.id, a.flujo]))
        const corte = new Set(view.flow.corte_minimo.map((c) => c.id))
        const maxF = Math.max(1, ...view.flow.aristas_flujo.map((a) => a.flujo))
        const activos = new Set<string>([view.flow.origen, view.flow.destino])
        view.flow.aristas_flujo.forEach((a) => { activos.add(a.source); activos.add(a.target) })
        cy.edges().forEach((e) => {
          const f = flujo.get(e.id())
          if (corte.has(e.id())) e.addClass('cut')
          else if (f) { e.addClass('flow'); e.style('width', 2 + (f / maxF) * 9) }
          else e.addClass('faded')
        })
        cy.nodes().forEach((n) => {
          if (!activos.has(n.id())) n.addClass('faded')
          else if (n.id() === view.flow!.origen || n.id() === view.flow!.destino) n.addClass('path')
        })
      }

      if (view.mode === 'dfs' && view.dfs?.encontrada) {
        const nodos = view.dfs.nodos
        const k = view.pathStep
        const enRuta = new Set(nodos.slice(0, k))
        const aristasRuta = new Set<string>()
        for (let i = 0; i < k - 1; i++) {
          const a = nodos[i], b = nodos[i + 1]
          cy.edges().forEach((e) => {
            const s = e.source().id(), t = e.target().id()
            if ((s === a && t === b) || (s === b && t === a)) aristasRuta.add(e.id())
          })
        }
        cy.nodes().forEach((n) => { n.addClass(enRuta.has(n.id()) ? 'path' : 'faded') })
        cy.edges().forEach((e) => { e.addClass(aristasRuta.has(e.id()) ? 'path' : 'faded') })
      }

      if (view.koGenes.length) {
        const ko = new Set(view.koGenes)
        view.koGenes.forEach((g) => cy.getElementById(g).addClass('ko'))
        cy.edges().forEach((e) => {
          if (ko.has(e.source().id()) || ko.has(e.target().id())) e.addClass('edgefaded')
        })
        if (view.ko) {
          view.ko.proteinas_aisladas.forEach((g) => cy.getElementById(g).addClass('isolated'))
          view.ko.pares_semilla_desconectados.forEach(([a, b]) => {
            cy.getElementById(a).addClass('pair')
            cy.getElementById(b).addClass('pair')
          })
        }
      }
    })
  }, [view, graph])

  // Atajo de teclado R = re-centrar
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement
      if (t.tagName === 'INPUT' || t.tagName === 'SELECT' || t.tagName === 'TEXTAREA') return
      if (e.key === 'r' || e.key === 'R') recentrar()
    }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [recentrar])

  const zoom = (f: number) => {
    const cy = cyRef.current
    if (!cy) return
    cy.animate({ zoom: { level: cy.zoom() * f, renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 } }, duration: 200 })
  }

  const exportarPng = () => {
    const cy = cyRef.current
    if (!cy) return
    const a = document.createElement('a')
    a.href = cy.png({ full: true, bg: '#000814', scale: 2 })
    a.download = `red_proteinas_${graph.via}_${graph.min_score}.png`
    a.click()
  }

  const btn = 'p-2 rounded-md bg-[#02101f]/90 border panel-borde hover:border-[#00e5ff] hover:text-[#00e5ff] transition'

  return (
    <div className="relative h-full w-full canvas-bg">
      <CytoscapeComponent
        elements={elements}
        stylesheet={STYLESHEET}
        cy={onCy}
        style={{ width: '100%', height: '100%' }}
        minZoom={0.1}
        maxZoom={4}
        wheelSensitivity={0.25}
      />
      {tip && (
        <div
          className="pointer-events-none absolute z-20 rounded-md border panel-borde bg-[#02101f]/95 px-2 py-1 text-xs shadow-lg"
          style={{ left: tip.x + 14, top: tip.y - 10 }}
        >
          <b>{tip.id}</b>
          <div className="text-slate-300">association_score: {tip.score.toFixed(3)}</div>
        </div>
      )}
      <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-2">
        <button className={btn} title="Acercar" onClick={() => zoom(1.3)}><Plus size={16} /></button>
        <button className={btn} title="Alejar" onClick={() => zoom(1 / 1.3)}><Minus size={16} /></button>
        <button className={btn} title="Re-centrar (R)" onClick={recentrar}><LocateFixed size={16} /></button>
        <button className={btn} title="Exportar PNG" onClick={exportarPng}><Download size={16} /></button>
      </div>
      <div className="absolute bottom-4 left-4 z-10 rounded-md bg-[#02101f]/80 px-2 py-1 text-[11px] text-slate-400">
        {graph.total_nodos} nodos · {graph.total_aristas} aristas · R = re-centrar
      </div>
    </div>
  )
}
