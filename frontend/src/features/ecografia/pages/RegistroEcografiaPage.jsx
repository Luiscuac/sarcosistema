import { Navigate, useParams } from 'react-router-dom'
import MarcoEcografia, { migasEstudio } from '../components/MarcoEcografia.jsx'
import InformeLibreEcografia from '../components/InformeLibreEcografia.jsx'
import RegistroHallazgos from '../components/registro/RegistroHallazgos.jsx'
import { useEstudioEcografia, usaPlantilla } from '../hooks/useEstudioEcografia.js'
import '../../laboratorio/pages/area-resultados.css'

/** Registro de hallazgos (como "Capturar resultados" de Laboratorio). */
export default function RegistroEcografiaPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const consulta = useEstudioEcografia(estudioId)
  const estudio = consulta.data
  if (estudio?.estado === 'publicado' && usaPlantilla(estudio)) return <Navigate to={`/ecografia/estudios/${estudioId}/informe`} replace />
  const navegacion = { volverA: `/ecografia/estudios/${estudioId}`, textoVolver: 'Volver al estudio', migas: migasEstudio(estudio, 'Registro') }
  return <MarcoEcografia usuario={usuario} logout={logout} navegacion={navegacion} clase="lab-area-results-page">
    {consulta.isPending && <p role="status">Cargando estudio…</p>}
    {consulta.isError && <p role="alert">No se pudo cargar el estudio. Vuelve a la bandeja e inténtalo de nuevo.</p>}
    {estudio && (usaPlantilla(estudio) ? <RegistroHallazgos key={estudioId} estudio={estudio} /> : <InformeLibreEcografia key={estudioId} estudio={estudio} />)}
  </MarcoEcografia>
}
