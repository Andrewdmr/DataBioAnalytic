import { X } from 'lucide-react'

const PASOS = [
  {
    numero: 1,
    titulo: 'Filtrar vía y confianza',
    icono: '🔍',
    texto: 'Elige una vía biológica y el umbral STRING Confidence Score para reducir el ruido y centrar la red.',
  },
  {
    numero: 2,
    titulo: 'Analizar conectividad',
    icono: '🌐',
    texto: 'Ejecuta Union-Find para ver islas funcionales o MST para quedarte con la columna vertebral de máxima confianza.',
  },
  {
    numero: 3,
    titulo: 'Trazar rutas y flujo',
    icono: '➡️',
    texto: 'Con DFS sigue la cascada de señalización entre dos genes; con Ford-Fulkerson mide su capacidad máxima y el Corte Mínimo.',
  },
  {
    numero: 4,
    titulo: 'Simular inhibición',
    icono: '🧪',
    texto: 'Aplica Knockout a genes clave y observa si la red se fragmenta o si existen rutas alternativas redundantes.',
  },
]

interface Props {
  abierta: boolean
  onCerrar: () => void
}

export default function GuiaRapida(p: Props) {
  if (!p.abierta) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={p.onCerrar}
      />
      <div className="relative w-full max-w-md bg-[#111827] border border-[#1E293B] rounded-2xl p-6 shadow-2xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold text-[#f1f5f9]">Guía rápida de uso · 4 pasos</h2>
          <button onClick={p.onCerrar} className="rounded p-1.5 hover:bg-[#1E293B] text-[#94a3b8]">
            <X size={20} />
          </button>
        </div>
        <ol className="space-y-4">
          {PASOS.map((paso) => (
            <li key={paso.numero} className="flex gap-3">
              <div className="shrink-0 w-8 h-8 rounded-full border border-[#1E293B] bg-[#1E293B] flex items-center justify-center text-xs font-bold text-[#0ea5e9]">
                {paso.numero}
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-lg">{paso.icono}</span>
                  <span className="font-semibold text-[#f1f5f9]">{paso.titulo}</span>
                </div>
                <p className="mt-0.5 text-sm text-[#94a3b8] leading-relaxed">{paso.texto}</p>
              </div>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-xs text-[#64748b] italic">
          También puedes ejecutar cada paso directamente desde el panel izquierdo y la barra superior.
        </p>
      </div>
    </div>
  )
}
