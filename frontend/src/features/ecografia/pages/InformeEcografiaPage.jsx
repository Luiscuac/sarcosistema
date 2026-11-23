import { useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import MarcoEcografia, { migasEstudio } from '../components/MarcoEcografia.jsx'
import InformeLibreEcografia from '../components/InformeLibreEcografia.jsx'
import InformeEcografiaDocumento from '../components/InformeEcografiaDocumento.jsx'
import { useEstudioEcografia, usaPlantilla } from '../hooks/useEstudioEcografia.js'
import { iniciarDatos } from '../informe.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import '../../laboratorio/pages/informe-solicitud.css'

/** Informe (borrador o publicado) listo para imprimir, como el informe final de Laboratorio. */
export default function InformeEcografiaPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const consulta = useEstudioEcografia(estudioId)
  const { notificar } = useNotificacion()
  const documento = useRef(null)
  const estudio = consulta.data
  const publicado = estudio?.estado === 'publicado'

  async function imprimir() {
    if (documento.current.querySelector('[role="status"], [role="alert"]')) { notificar('Espera a que todas las imágenes estén disponibles antes de imprimir.', 'error'); return }
    try { await Promise.all([...documento.current.querySelectorAll('img')].map(img => img.decode())); window.print() }
    catch { notificar('Una imagen no pudo cargarse. Reintenta antes de imprimir.', 'error') }
  }

  const navegacion = { volverA: `/ecografia/estudios/${estudioId}`, textoVolver: 'Volver al estudio', migas: migasEstudio(estudio, 'Informe') }
  return <MarcoEcografia usuario={usuario} logout={logout} navegacion={navegacion} clase="lab-report-page">
    {consulta.isPending && <p role="status">Cargando informe…</p>}
    {consulta.isError && <p role="alert">No se pudo cargar el informe. Vuelve a la bandeja e inténtalo de nuevo.</p>}
    {estudio && !usaPlantilla(estudio) && <InformeLibreEcografia key={estudioId} estudio={estudio} />}
    {estudio && usaPlantilla(estudio) && !estudio.informe && <div className="lab-detail-card"><h2>Todavía no hay informe</h2><p>Registra los hallazgos para generar el informe.</p>
      <Link className="primary-button" to={`/ecografia/estudios/${estudioId}/registro`}>Registrar hallazgos</Link></div>}
    {estudio?.informe && usaPlantilla(estudio) && <>
      <div className="lab-report-controls">
        <p className="eco-informe-estado">{publicado ? 'Informe publicado' : 'Borrador: así se verá al publicarlo.'}</p>
        <div className="eco-informe-acciones">
          {!publicado && <Link className="lab-secondary-button" to={`/ecografia/estudios/${estudioId}/registro`}>Seguir editando</Link>}
          <button className="primary-button" type="button" onClick={imprimir}>Imprimir o guardar PDF</button>
        </div>
      </div>
      <InformeEcografiaDocumento estudio={estudio} datos={iniciarDatos(estudio)} guardados={estudio.informe.archivos || []} archivos={[]}
        publicado={publicado} documentoRef={documento} />
    </>}
  </MarcoEcografia>
}
