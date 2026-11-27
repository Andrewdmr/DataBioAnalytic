import { useMemo, useState } from 'react'
import { Dna, HelpCircle, Info, Search } from 'lucide-react'

export const VIAS: { value: string; label: string; color: string }[] = [
  { value: 'todas', label: 'Todas', color: '#94a3b8' },
  { value: 'ciclo_y_apoptosis', label: 'Ciclo Celular y Apoptosis', color: '#10b981' },
  { value: 'senalizacion_hormonal', label: 'Señalización Hormonal', color: '#0ea5e9' },
  { value: 'reparacion_adn', label: 'Reparación de ADN', color: '#f43f5e' },
]

interface Props {
  via: string
  onVia: (v: string) => void
  minScore: number
  onMinScore: (v: number) => void
  maxNodos: number
  onMaxNodos: (v: number) => void
  genes: string[]
  onPick: (id: string) => void
  loading: boolean
  onAbrirGuia: () => void
}

const help = (label: string) => (
  <span className="help-icon" title={label}>
    <Info size={13} className="text-[#94a3b8]" />
  </span>
)

export default function TopBar(p: Props) {
  const [q, setQ] = useState('')
  const [abierto, setAbierto] = useState(false)

  const coincidencias = useMemo(() => {
    const t = q.trim().toUpperCase()
    if (!t) return []
    const empieza = p.genes.filter((g) => g.startsWith(t))
    const contiene = p.genes.filter((g) => !g.startsWith(t) && g.includes(t))
    return [...empieza, ...contiene].slice(0, 8)
  }, [q, p.genes])

  const elegir = (g: string) => {
    p.onPick(g)
    setQ(g)
    setAbierto(false)
  }

  return (
    <header className="flex h-14 shrink-0 items-center gap-4 border-b border-[#1E293B] bg-[#111827] backdrop-blur-md px-4 text-sm">
      <div className="flex items-center gap-2 font-semibold text-[#0ea5e9]">
        <Dna size={18} /> Red de proteínas · cáncer de mama
      </div>

      <label className="flex items-center gap-2">
        <span className="text-[#94a3b8]">Vía</span>
        <select value={p.via} onChange={(e) => p.onVia(e.target.value)}>
          {VIAS.map((v) => (
            <option key={v.value} value={v.value} style={{ color: v.color }}>
              {v.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2">
        <span className="text-[#94a3b8]">STRING ≥</span>
        {help('Umbral mínimo de confianza de STRING. Valores más altos muestran solo interacciones de alta confianza y reducen el ruido de la red.')}
        <input type="range" min={400} max={999} value={p.minScore}
          onChange={(e) => p.onMinScore(Number(e.target.value))} className="w-36" />
        <span className="w-9 font-mono text-[#cbd5e1]">{p.minScore}</span>
      </label>

      <label className="flex items-center gap-2">
        <span className="text-[#94a3b8]">Nodos</span>
        {help('Límite máximo de proteínas cargadas en el subgrafo. Protege el rendimiento del navegador en redes grandes.')}
        <select value={p.maxNodos} onChange={(e) => p.onMaxNodos(Number(e.target.value))}>
          {[50, 100, 150, 250, 300].map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>

      <div className="relative ml-auto w-64">
        <Search size={14} className="absolute left-2 top-2 text-[#94a3b8]" />
        <input
          type="text" placeholder="Buscar gen (TP53, BRCA1…)" value={q}
          className="w-full !pl-7"
          onChange={(e) => { setQ(e.target.value); setAbierto(true) }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setTimeout(() => setAbierto(false), 150)}
          onKeyDown={(e) => { if (e.key === 'Enter' && coincidencias[0]) elegir(coincidencias[0]) }}
        />
        {abierto && coincidencias.length > 0 && (
          <ul className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-[#1E293B] bg-[#111827] shadow-xl">
            {coincidencias.map((g) => (
              <li key={g} onMouseDown={() => elegir(g)}
                  className="cursor-pointer px-3 py-1.5 hover:bg-[#273549]">{g}</li>
            ))}
          </ul>
        )}
      </div>

      <button onClick={p.onAbrirGuia} className="flex items-center gap-1.5 rounded-md border border-[#1E293B] bg-[#1E293B] px-3 py-1.5 text-xs font-medium text-[#0ea5e9] hover:bg-[#273549] transition">
        <HelpCircle size={16} /> Guía
      </button>
      {p.loading && <span className="text-xs text-[#f59e0b]">cargando…</span>}
    </header>
  )
}
