import { useParams } from 'react-router-dom'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import SeccionInforme from '../components/SeccionInforme.jsx'
import { navegacionEstudio, useEstudioRx } from '../hooks/useEstudioRx.js'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'
import '../../../laboratorio/pages/area-resultados.css'
import '../../asistente/pages/rayos-x.css'
import './estudio.css'

/** Informe: la placa a la izquierda y el formulario a la derecha (preferencia del servicio). */
export default function InformeRayosXPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const { data: detalle, isLoading, isError, error } = useEstudioRx(estudioId)
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacionEstudio(detalle, estudioId, 'Informe')} clase="rx-trabajo">
    {isLoading && <p role="status">Cargando estudio…</p>}
    {isError && <p role="alert" className="lab-form-error">{mensajeError(error, 'No se pudo cargar el estudio.')}</p>}
    {detalle && <>
      <header className="lab-area-results-header">
        <p className="lab-eyebrow">INFORME · {detalle.estudio.referencia_estudio}</p>
        <h1>{detalle.estudio.tipo_estudio_nombre}</h1>
        <p>{detalle.paciente.nombre_completo} · {detalle.paciente.edad ?? '—'} / {detalle.paciente.sexo || '—'}{detalle.estudio.detalle?.indicacion_clinica ? ` · ${detalle.estudio.detalle.indicacion_clinica}` : ''}{detalle.estudio.prioridad === 'urgente' ? ' · Urgente' : ''}</p>
      </header>
      <SeccionInforme estudioId={estudioId} detalle={detalle} />
    </>}
  </RayosXLayout>
}
