import { pasoActualRx } from '../utils/flujo.js'

const PASOS = ['Solicitud', 'Adquisición', 'Informe', 'Entrega']

/** Etapas del estudio con el estilo de Laboratorio: Solicitud → Adquisición → Informe → Entrega. */
export default function RecorridoRx({ etapa }) {
  if (etapa === 'no_realizado' || etapa === 'anulado') {
    return <span className="lab-steps lab-steps--closed rx-recorrido-cerrado">{etapa === 'anulado' ? 'Anulado' : 'Cerrado sin realizar'}</span>
  }
  const actual = pasoActualRx(etapa)
  return <ol className="lab-steps rx-recorrido" aria-label="Etapas del estudio">
    {PASOS.map((paso, i) => {
      const e = i < actual ? 'done' : i === actual ? 'current' : 'todo'
      return <li key={paso} className={`lab-step lab-step--${e}`} aria-current={e === 'current' ? 'step' : undefined}>
        <span aria-hidden="true">{e === 'done' ? '✓' : i + 1}</span>{paso}
        <span className="sr-only">{e === 'done' ? ' (completado)' : e === 'current' ? ' (en curso)' : ' (pendiente)'}</span>
      </li>
    })}
  </ol>
}
