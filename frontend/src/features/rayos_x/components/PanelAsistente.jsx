import { hallazgosDeVision, nombreHallazgo } from '../analisis.js'

const Barra = ({ valor, marcada }) => <span className={`rx-barra${marcada ? ' es-marcada' : ''}`} aria-hidden="true">
  <span style={{ width: `${Math.round(Math.min(1, Math.max(0, valor)) * 100)}%` }} />
</span>

function Hallazgo({ h, mapa, onMapa, conMapa }) {
  return <li className={h.above_operating_point ? 'es-destacado' : undefined}>
    <span className="rx-hallazgo-nombre">{nombreHallazgo(h.name)}</span>
    <Barra valor={h.score} marcada={h.above_operating_point} />
    <strong>{Number(h.score).toFixed(2)}</strong>
    {conMapa && <button type="button" className="rx-enlace" aria-pressed={mapa === h.name} onClick={() => onMapa(mapa === h.name ? null : h.name)}>
      {mapa === h.name ? 'Ocultar mapa' : 'Ver dónde'}
    </button>}
  </li>
}

/** Resumen del asistente: índice de prioridad, por qué, calidad de la imagen y las 18 categorías. */
export default function PanelAsistente({ vision, mapa, onMapa }) {
  const { todas, principales, completo } = hallazgosDeVision(vision)
  const indice = vision?.indice_pulmonar
  const calidad = vision?.calidad
  const conMapa = nombre => Boolean(vision?.mapas_calor?.mapas?.[nombre])
  const destacados = todas.filter(h => h.above_operating_point).length
  return <div className="rx-panel">
    {indice && <section className="rx-indice" aria-label="Índice de prioridad">
      <div className="rx-indice-cabecera">
        <h3>Índice de prioridad pulmonar</h3>
        <strong>{Math.round(indice.valor * 100)}<small>/100</small></strong>
      </div>
      <Barra valor={indice.valor} />
      <p className="rx-nota">Más alto = revisar antes. No es una probabilidad ni un diagnóstico de tuberculosis.</p>
      {indice.contribuciones?.length > 0 && <>
        <h4>Qué lo eleva</h4>
        <ul className="rx-contribuciones">{indice.contribuciones.map(c => <li key={c.name}>{nombreHallazgo(c.name)}<span>+{c.aporte.toFixed(2)}</span></li>)}</ul>
      </>}
      {conMapa('indice_pulmonar') && <button type="button" className="lab-secondary-button" aria-pressed={mapa === 'indice_pulmonar'}
        onClick={() => onMapa(mapa === 'indice_pulmonar' ? null : 'indice_pulmonar')}>
        {mapa === 'indice_pulmonar' ? 'Ocultar mapa del índice' : 'Ver dónde mira el modelo'}
      </button>}
    </section>}
    {calidad && <section className={`rx-calidad es-${calidad.estado}`} aria-label="Calidad de la imagen">
      <h3>Calidad de la imagen: {calidad.estado === 'ok' ? 'adecuada' : 'revisar'}</h3>
      {calidad.avisos?.length ? <ul>{calidad.avisos.map(a => <li key={a}>{a}</li>)}</ul> : <p>Sin avisos de entrada.</p>}
    </section>}
    <section aria-label="Hallazgos del modelo">
      <h3>Hallazgos del modelo experimental</h3>
      <p className="rx-nota">Scores normalizados (0,5 = punto técnico del modelo), no porcentajes de certeza.</p>
      <ul className="rx-hallazgos">{principales.map(h => <Hallazgo key={h.name} h={h} mapa={mapa} onMapa={onMapa} conMapa={conMapa(h.name)} />)}</ul>
      {completo && <details className="rx-todas">
        <summary>Las 18 categorías del modelo{destacados ? ` · ${destacados} sobre el punto técnico` : ''}</summary>
        <ul className="rx-hallazgos">{todas.map(h => <Hallazgo key={h.name} h={h} mapa={mapa} onMapa={onMapa} conMapa={conMapa(h.name)} />)}</ul>
      </details>}
    </section>
  </div>
}
