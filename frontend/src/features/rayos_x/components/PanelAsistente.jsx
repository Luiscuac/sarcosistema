import { nivelSenal, nombreHallazgo, sugerenciasDeVision, VEREDICTOS } from '../analisis.js'

/** Indicador de nivel con texto: nunca depende solo del color. */
function Nivel({ score }) {
  const nivel = nivelSenal(score)
  return <span className={`rx-ia-nivel es-${nivel.clave}`}><span className="rx-ia-puntos" aria-hidden="true"><i /><i /><i /></span>{nivel.texto}</span>
}

function BotonMapa({ nombre, mapa, onMapa }) {
  const activo = mapa === nombre
  return <button type="button" className="rx-ia-ver" aria-pressed={activo} onClick={() => onMapa(activo ? null : nombre)}>
    {activo ? 'Ocultar en la imagen' : 'Ver en la imagen'}
  </button>
}

/** Veredicto en lenguaje simple: lo primero que lee el médico. */
export function VeredictoAsistente({ vision, prioridad }) {
  const { principales } = sugerenciasDeVision(vision)
  const clave = prioridad || (principales.length ? 'media' : 'baja')
  const veredicto = VEREDICTOS[clave]
  const calidad = vision?.calidad
  const indice = vision?.indice_pulmonar?.valor
  return <section className={`rx-ia-veredicto es-${clave}`} aria-label="Resultado del asistente">
    <p className="rx-ia-etiqueta">Resultado del asistente · orientativo</p>
    <h3>{veredicto.titulo}</h3>
    <p>{principales.length
      ? <>El modelo asocia la imagen principalmente con <strong>{principales.map(h => nombreHallazgo(h.name)).join(', ')}</strong>.</>
      : 'Ningún hallazgo supera el punto de corte del modelo.'} {veredicto.texto}</p>
    <dl className="rx-ia-datos">
      {typeof indice === 'number' && <div><dt>Índice de prioridad</dt><dd>{Math.round(indice * 100)} de 100</dd></div>}
      {calidad && <div><dt>Calidad de la imagen</dt><dd className={calidad.estado === 'ok' ? undefined : 'es-aviso'}>{calidad.estado === 'ok' ? 'Adecuada' : 'Revisar'}</dd></div>}
    </dl>
    {calidad?.estado !== 'ok' && calidad?.avisos?.length > 0 && <ul className="rx-ia-avisos-calidad">{calidad.avisos.map(a => <li key={a}>{a}</li>)}</ul>}
  </section>
}

/** Sugerencias: las 3 señales más fuertes; el resto plegado como señales secundarias. */
export default function PanelAsistente({ vision, mapa, onMapa }) {
  const { principales, debiles, sinSenal } = sugerenciasDeVision(vision)
  const conMapa = nombre => Boolean(vision?.mapas_calor?.mapas?.[nombre])
  const contribuciones = vision?.indice_pulmonar?.contribuciones || []
  return <div className="rx-ia-hallazgos">
    <h4>Sugerencias principales</h4>
    <p className="rx-nota">Hallazgos a los que más se parece la imagen según el modelo. Son una guía para tu lectura, no un diagnóstico.</p>
    {principales.length > 0
      ? <ol className="rx-ia-lista es-sugerencias">{principales.map(h => <li key={h.name}>
          <strong>{nombreHallazgo(h.name)}</strong><Nivel score={h.score} />
          {conMapa(h.name) && <BotonMapa nombre={h.name} mapa={mapa} onMapa={onMapa} />}
        </li>)}</ol>
      : <p className="rx-ia-vacio">El modelo no asocia la imagen con ningún hallazgo por encima de su punto de corte.</p>}
    {debiles.length > 0 && <details className="rx-ia-plegable">
      <summary>Otras {debiles.length} señales secundarias · suelen ser falsas alarmas</summary>
      <p className="rx-nota">Cuando una imagen es anormal, el modelo tiende a activar varias categorías a la vez. Revísalas solo si coinciden con lo que ves.</p>
      <ul className="rx-ia-lista es-compacta">{debiles.map(h => <li key={h.name}><span>{nombreHallazgo(h.name)}</span><Nivel score={h.score} />
        {conMapa(h.name) && <BotonMapa nombre={h.name} mapa={mapa} onMapa={onMapa} />}</li>)}</ul>
    </details>}
    {contribuciones.length > 0 && <div className="rx-ia-indice">
      <h4>Qué eleva el índice de prioridad</h4>
      <p>{contribuciones.map(c => nombreHallazgo(c.name)).join(', ')}.</p>
      {conMapa('indice_pulmonar') && <BotonMapa nombre="indice_pulmonar" mapa={mapa} onMapa={onMapa} />}
    </div>}
    {sinSenal.length > 0 && <details className="rx-ia-plegable">
      <summary>{sinSenal.length} hallazgos revisados sin señal relevante</summary>
      <ul className="rx-ia-lista es-compacta">{sinSenal.map(h => <li key={h.name}><span>{nombreHallazgo(h.name)}</span><Nivel score={h.score} /></li>)}</ul>
    </details>}
  </div>
}
