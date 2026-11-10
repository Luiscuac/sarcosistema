import { descargarArchivoImagen } from '../api/consultasApi.js'
import { esDescargable, etiquetaArchivo, formatearTamano } from '../utils/examenes.js'
import { fecha } from '../utils/paciente.js'

/**
 * Resultados de ecografía del paciente: solo informes publicados por el servicio de imagen.
 * Siempre muestra el panel (con carga, error o "sin resultados") para separarlo de la solicitud.
 */
export default function ExamenesComplementarios({ historial, ejemplo = null }) {
  const estudios = historial.data?.estudios_imagen ?? []
  return (
    <section className="med-panel med-eco-results">
      <div className="med-panel-header">
        <div><h2>Resultados de ecografía</h2><span>Informes publicados por el servicio de imagen</span></div>
        {estudios.length > 0 && <span className="med-eco-count">{estudios.length} {estudios.length === 1 ? 'informe' : 'informes'}</span>}
      </div>
      {historial.isPending && <p role="status" className="med-message">Cargando resultados…</p>}
      {historial.isError && <p role="alert" className="med-message">No se pudieron cargar los resultados de ecografía.</p>}
      {historial.data && !estudios.length && <p className="med-message">Todavía no hay ecografías informadas para este paciente. Las que solicites aparecerán aquí cuando el servicio de imagen publique el informe.</p>}
      {estudios.map((estudio) => (
        <article className="med-eco-estudio" key={estudio.estudio_id}>
          <header>
            <strong>{estudio.tipo_estudio_nombre}</strong>
            <span>Publicado el {fecha(estudio.fecha_publicacion)} · {estudio.referencia_estudio}</span>
          </header>
          {estudio.descripcion_texto
            ? <p className="med-eco-informe">{estudio.descripcion_texto}</p>
            : <p className="med-message">El informe no tiene texto registrado.</p>}
          {estudio.archivos?.length ? (
            <ul className="med-eco-archivos">
              {estudio.archivos.map((archivo) => (
                <li key={archivo.id}>
                  <span>{etiquetaArchivo(archivo.mime_type, archivo.nombre_original)}</span>
                  <small>{formatearTamano(archivo.tamano_bytes)}</small>
                  <button
                    type="button"
                    className="med-secondary-button"
                    onClick={() => descargarArchivoImagen(archivo.id, archivo.nombre_original)}
                  >
                    {esDescargable(archivo.mime_type) ? 'Descargar' : 'Ver / descargar'}
                  </button>
                </li>
              ))}
            </ul>
          ) : <p className="med-message">Este estudio no tiene archivos adjuntos.</p>}
        </article>
      ))}
      {ejemplo}
    </section>
  )
}
