const PASOS = ['Solicitado', 'Registro', 'Publicado']

/** Etapas del estudio con el estilo de Laboratorio: Solicitado → Registro → Publicado. */
export default function RecorridoEco({ estado }) {
  const actual = estado === 'publicado' ? 3 : 1
  return <ol className="lab-steps eco-recorrido" aria-label="Etapas del estudio">
    {PASOS.map((paso, i) => {
      const e = i < actual ? 'done' : i === actual ? 'current' : 'todo'
      return <li key={paso} className={`lab-step lab-step--${e}`} aria-current={e === 'current' ? 'step' : undefined}>
        <span aria-hidden="true">{e === 'done' ? '✓' : i + 1}</span>{paso}
        <span className="sr-only">{e === 'done' ? ' (completado)' : e === 'current' ? ' (en curso)' : ' (pendiente)'}</span>
      </li>
    })}
  </ol>
}
