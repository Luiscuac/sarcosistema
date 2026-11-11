import { Link } from 'react-router-dom'
import { fecha } from '../utils/paciente.js'

/**
 * Resultados de ecografía del paciente: solo informes publicados por el servicio de imagen.
 * Siempre muestra el panel (con carga, error o "sin resultados") para separarlo de la solicitud.
 */
export default function ExamenesComplementarios({ historial, pacienteId, modalidad = 'ecografia', ejemplo = null }) {
  const rayosX = modalidad === 'rayos_x'
  const nombre = rayosX ? 'Rayos X' : 'ecografía'
  const estudios = (historial.data?.estudios_imagen ?? []).filter(estudio => rayosX
    ? /radiograf|rayos x/i.test(estudio.tipo_estudio_nombre)
    : /ecograf/i.test(estudio.tipo_estudio_nombre))
  return (
    <section className="med-panel med-eco-results">
      <div className="med-panel-header">
        <div><h2>Resultados de {nombre}</h2><span>Informes publicados por el servicio de imagen</span></div>
        {estudios.length > 0 && <span className="med-eco-count">{estudios.length} {estudios.length === 1 ? 'informe' : 'informes'}</span>}
      </div>
      {historial.isPending && <p role="status" className="med-message">Cargando resultados…</p>}
      {historial.isError && <p role="alert" className="med-message">No se pudieron cargar los resultados de {nombre}.</p>}
      {historial.data && !estudios.length && <p className="med-message">Todavía no hay estudios de {nombre} informados para este paciente. Los que solicites aparecerán aquí cuando el servicio de imagen publique el informe.</p>}
      {estudios.map((estudio) => (
        <article className="med-eco-estudio" key={estudio.estudio_id}>
          <header>
            <strong>{estudio.tipo_estudio_nombre}</strong>
            <span>Publicado el {fecha(estudio.fecha_publicacion)} · {estudio.referencia_estudio}</span>
          </header>
          {estudio.descripcion_texto
            ? <p className="med-eco-informe">{estudio.descripcion_texto.length > 220 ? `${estudio.descripcion_texto.slice(0, 220).trimEnd()}…` : estudio.descripcion_texto}</p>
            : <p className="med-message">El informe no tiene texto registrado.</p>}
          <div className="med-eco-acciones"><span>{estudio.archivos?.length || 0} archivos adjuntos</span><Link className="med-lab-report-button" to={`/consultas/pacientes/${pacienteId}/${rayosX ? 'rayos-x' : 'ecografias'}/${estudio.estudio_id}/informe`}>Ver informe</Link></div>
        </article>
      ))}
      {ejemplo}
    </section>
  )
}
