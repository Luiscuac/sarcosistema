import { descargarArchivoImagen } from '../api/consultasApi.js'
import { esDescargable, etiquetaArchivo, formatearTamano } from '../utils/examenes.js'

function fecha(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO') : 'Sin fecha'
}

/** Reporte de examenes complementarios del paciente: solo estudios publicados. */
export default function ExamenesComplementarios({ estudios }) {
  if (!estudios?.length) return null
  return (
    <section className="med-panel">
      <div className="med-panel-header">
        <h2>Exámenes complementarios</h2>
        <span>Ecografías publicadas por el servicio de imagen</span>
      </div>
      {estudios.map((estudio) => (
        <article className="med-eco-estudio" key={estudio.estudio_id}>
          <header>
            <strong>{estudio.tipo_estudio_nombre}</strong>
            <span>{fecha(estudio.fecha_publicacion)} · {estudio.referencia_estudio}</span>
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
                    className="med-button-link"
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
    </section>
  )
}
