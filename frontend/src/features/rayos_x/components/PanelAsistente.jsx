import { hallazgosDeVision, nivelSenal, nombreHallazgo, VEREDICTOS } from '../analisis.js'

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
  const { todas } = hallazgosDeVision(vision)
  const destacados = todas.filter(h => h.above_operating_point)
  const clave = prioridad || (destacados.length ? 'media' : 'baja')
  const veredicto = VEREDICTOS[clave]
  const calidad = vision?.calidad
  const indice = vision?.indice_pulmonar?.valor
  return <section className={`rx-ia-veredicto es-${clave}`} aria-label="Resultado del asistente">
    <p className="rx-ia-etiqueta">Resultado del asistente · orientativo</p>
    <h3>{veredicto.titulo}</h3>
    <p>{destacados.length
      ? <>Destaca <strong>{destacados.slice(0, 3).map(h => nombreHallazgo(h.name)).join(', ')}</strong>{destacados.length > 3 ? ` y ${destacados.length - 3} más` : ''}.</>
      : 'Ningún hallazgo supera el punto de corte del modelo.'} {veredicto.texto}</p>
    <dl className="rx-ia-datos">
      {typeof indice === 'number' && <div><dt>Índice de prioridad</dt><dd>{Math.round(indice * 100)} de 100</dd></div>}
      {calidad && <div><dt>Calidad de la imagen</dt><dd className={calidad.estado === 'ok' ? undefined : 'es-aviso'}>{calidad.estado === 'ok' ? 'Adecuada' : 'Revisar'}</dd></div>}
    </dl>
    {calidad?.estado !== 'ok' && calidad?.avisos?.length > 0 && <ul className="rx-ia-avisos-calidad">{calidad.avisos.map(a => <li key={a}>{a}</li>)}</ul>}
  </section>
}

/** Hallazgos: primero los destacados, luego el resto plegado. Sin barras ni números sueltos. */
export default function PanelAsistente({ vision, mapa, onMapa }) {
  const { todas } = hallazgosDeVision(vision)
  const conMapa = nombre => Boolean(vision?.mapas_calor?.mapas?.[nombre])
  const destacados = todas.filter(h => h.above_operating_point)
  const resto = todas.filter(h => !h.above_operating_point)
  const contribuciones = vision?.indice_pulmonar?.contribuciones || []
  return <div className="rx-ia-hallazgos">
    <p className="rx-nota">La señal indica cuánto se parece la imagen a cada hallazgo según el modelo. No es una probabilidad ni un diagnóstico.</p>
    {destacados.length > 0
      ? <ul className="rx-ia-lista">{destacados.map(h => <li key={h.name}>
          <strong>{nombreHallazgo(h.name)}</strong><Nivel score={h.score} />
          {conMapa(h.name) && <BotonMapa nombre={h.name} mapa={mapa} onMapa={onMapa} />}
        </li>)}</ul>
      : <p className="rx-ia-vacio">Ningún hallazgo supera el punto de corte del modelo.</p>}
    {contribuciones.length > 0 && <div className="rx-ia-indice">
      <h4>Qué eleva el índice de prioridad</h4>
      <p>{contribuciones.map(c => nombreHallazgo(c.name)).join(', ')}.</p>
      {conMapa('indice_pulmonar') && <BotonMapa nombre="indice_pulmonar" mapa={mapa} onMapa={onMapa} />}
    </div>}
    {resto.length > 0 && <details className="rx-ia-plegable">
      <summary>Otros {resto.length} hallazgos revisados sin señal relevante</summary>
      <ul className="rx-ia-lista es-compacta">{resto.map(h => <li key={h.name}><span>{nombreHallazgo(h.name)}</span><Nivel score={h.score} /></li>)}</ul>
    </details>}
  </div>
}
