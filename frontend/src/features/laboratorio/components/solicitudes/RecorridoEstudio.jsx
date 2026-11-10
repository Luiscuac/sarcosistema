const PASOS = ['Muestra', 'Resultado', 'Publicado']
const PASO_ACTUAL = { pendiente_muestra: 0, resultado_en_preparacion: 1, publicado: 3 }

/** Muestra en qué etapa está un estudio: Muestra → Resultado → Publicado. */
export default function RecorridoEstudio({ estado }) {
  if (estado === 'no_realizado') {
    return <span className="lab-steps lab-steps--closed">Cerrado sin resultado</span>
  }
  const actual = PASO_ACTUAL[estado] ?? 0
  return (
    <ol className="lab-steps" aria-label="Etapas del estudio">
      {PASOS.map((paso, indice) => {
        const estadoPaso = indice < actual ? 'done' : indice === actual ? 'current' : 'todo'
        return <li key={paso} className={`lab-step lab-step--${estadoPaso}`} aria-current={estadoPaso === 'current' ? 'step' : undefined}>
          <span aria-hidden="true">{estadoPaso === 'done' ? '✓' : indice + 1}</span>{paso}
          <span className="sr-only">{estadoPaso === 'done' ? ' (completado)' : estadoPaso === 'current' ? ' (en curso)' : ' (pendiente)'}</span>
        </li>
      })}
    </ol>
  )
}
