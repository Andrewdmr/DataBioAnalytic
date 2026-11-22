import { useMemo, useState } from 'react'
import { Dna, Search } from 'lucide-react'

export const VIAS: { value: string; label: string }[] = [
  { value: 'todas', label: 'Todas' },
  { value: 'ciclo_y_apoptosis', label: 'Ciclo Celular y Apoptosis' },
  { value: 'senalizacion_hormonal', label: 'Señalización Hormonal' },
  { value: 'reparacion_adn', label: 'Reparación de ADN' },
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
}

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
    <header className="flex h-14 shrink-0 items-center gap-5 border-b-2 border-white px-4 text-sm">
      <div className="flex items-center gap-2 font-semibold text-[#00e5ff]">
        <Dna size={18} /> Red de proteínas · cáncer de mama
      </div>

      <label className="flex items-center gap-2">
        <span className="text-slate-400">Vía</span>
        <select value={p.via} onChange={(e) => p.onVia(e.target.value)}>
          {VIAS.map((v) => <option key={v.value} value={v.value}>{v.label}</option>)}
        </select>
      </label>

      <label className="flex items-center gap-2">
        <span className="text-slate-400">STRING ≥</span>
        <input type="range" min={400} max={999} value={p.minScore}
               onChange={(e) => p.onMinScore(Number(e.target.value))} className="w-36" />
        <span className="w-9 font-mono text-[#aaff00]">{p.minScore}</span>
      </label>

      <label className="flex items-center gap-2">
        <span className="text-slate-400">Nodos</span>
        <select value={p.maxNodos} onChange={(e) => p.onMaxNodos(Number(e.target.value))}>
          {[50, 100, 150, 250, 300].map((n) => <option key={n} value={n}>{n}</option>)}
        </select>
      </label>

      <div className="relative ml-auto w-64">
        <Search size={14} className="absolute left-2 top-2 text-slate-500" />
        <input
          type="text" placeholder="Buscar gen (TP53, BRCA1…)" value={q}
          className="w-full !pl-7"
          onChange={(e) => { setQ(e.target.value); setAbierto(true) }}
          onFocus={() => setAbierto(true)}
          onBlur={() => setTimeout(() => setAbierto(false), 150)}
          onKeyDown={(e) => { if (e.key === 'Enter' && coincidencias[0]) elegir(coincidencias[0]) }}
        />
        {abierto && coincidencias.length > 0 && (
          <ul className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border panel-borde bg-[#02101f] shadow-xl">
            {coincidencias.map((g) => (
              <li key={g} onMouseDown={() => elegir(g)}
                  className="cursor-pointer px-3 py-1.5 hover:bg-[#0a2a4a]">{g}</li>
            ))}
          </ul>
        )}
      </div>
      {p.loading && <span className="text-xs text-[#ffbb00]">cargando…</span>}
    </header>
  )
}
