import { avisosDeFusion, mencionesDelInforme, nombreHallazgo } from '../analisis.js'

const ESTADOS = { descrito: 'descrito', negado: 'negado', incierto: 'incierto', ambiguo: 'ambiguo o contradictorio' }
const TITULOS = {
  discrepancia: 'Discrepancia: el informe lo niega y el modelo lo destaca',
  posible_omision: 'Posible omisión: el modelo lo destaca y el informe no lo menciona',
  coincidencia: 'Coincidencia: descrito en el informe y destacado por el modelo',
}

/** Comparación informe ↔ imagen: qué dice el informe y qué conviene revisar. */
export default function PanelInforme({ fusion, mapa, onMapa, conMapa }) {
  const menciones = mencionesDelInforme(fusion)
  const avisos = avisosDeFusion(fusion)
  const ocultas = (fusion?.omisiones_totales || 0) - (fusion?.posibles_omisiones?.length || 0)
  return <section className="rx-panel-informe" aria-label="Comparación con el informe">
    <h3>Comparación con el informe</h3>
    <p className="rx-nota">Lectura por reglas de términos explícitos en {fusion?.criterio_tecnico?.categorias_comparadas || menciones.length} categorías. No interpreta el informe completo ni confirma diagnósticos.</p>
    {avisos.length > 0
      ? <ul className="rx-avisos">{avisos.map(a => <li key={`${a.tipo}-${a.hallazgo}`} className={`es-${a.tipo}`}>
        <strong>{nombreHallazgo(a.hallazgo)}</strong>
        <span>{TITULOS[a.tipo]}{typeof a.score === 'number' ? ` · score ${a.score.toFixed(2)}` : ''}</span>
        {conMapa(a.hallazgo) && <button type="button" className="rx-enlace" aria-pressed={mapa === a.hallazgo} onClick={() => onMapa(mapa === a.hallazgo ? null : a.hallazgo)}>{mapa === a.hallazgo ? 'Ocultar mapa' : 'Ver dónde'}</button>}
      </li>)}</ul>
      : <p>No se identificaron discrepancias, omisiones ni coincidencias en las categorías destacadas. Esto no descarta enfermedad.</p>}
    {ocultas > 0 && <p className="rx-nota">Hay {ocultas} posibles omisiones más con score menor; revisa la lista de 18 categorías.</p>}
    {menciones.length > 0 && <details className="rx-todas">
      <summary>Lo que dice el informe ({menciones.length} {menciones.length === 1 ? 'categoría mencionada' : 'categorías mencionadas'})</summary>
      <ul className="rx-menciones">{menciones.map(m => <li key={m.nombre}><strong>{nombreHallazgo(m.nombre)}: {ESTADOS[m.estado] || m.estado}</strong>
        {m.evidencia.map((e, i) => <blockquote key={i}>{e}</blockquote>)}</li>)}</ul>
    </details>}
  </section>
}
