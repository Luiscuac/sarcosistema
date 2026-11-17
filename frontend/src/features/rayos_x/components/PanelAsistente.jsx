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
    <h3>{veredicto.titulo}</h3>
    <p>{principales.length
      ? <>Se parece a: <strong>{principales.map(h => nombreHallazgo(h.name)).join(', ')}</strong></>
      : 'Sin hallazgos por encima del punto de corte.'}</p>
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
  return <div className="rx-ia-hallazgos">
    <h4>Sugerencias principales <small>· guía, no diagnóstico</small></h4>
    {principales.length > 0
      ? <ol className="rx-ia-lista es-sugerencias">{principales.map(h => <li key={h.name}>
          <strong>{nombreHallazgo(h.name)}</strong><Nivel score={h.score} />
          {conMapa(h.name) && <BotonMapa nombre={h.name} mapa={mapa} onMapa={onMapa} />}
        </li>)}</ol>
      : <p className="rx-ia-vacio">Sin sugerencias.</p>}
    {debiles.length > 0 && <details className="rx-ia-plegable">
      <summary>Otras {debiles.length} señales secundarias · suelen ser falsas alarmas</summary>
      <ul className="rx-ia-lista es-compacta">{debiles.map(h => <li key={h.name}><span>{nombreHallazgo(h.name)}</span><Nivel score={h.score} />
        {conMapa(h.name) && <BotonMapa nombre={h.name} mapa={mapa} onMapa={onMapa} />}</li>)}</ul>
    </details>}
    {sinSenal.length > 0 && <details className="rx-ia-plegable">
      <summary>{sinSenal.length} sin señal relevante</summary>
      <ul className="rx-ia-lista es-compacta">{sinSenal.map(h => <li key={h.name}><span>{nombreHallazgo(h.name)}</span><Nivel score={h.score} /></li>)}</ul>
    </details>}
  </div>
}
