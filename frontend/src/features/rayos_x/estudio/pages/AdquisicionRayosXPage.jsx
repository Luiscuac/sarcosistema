import { useParams } from 'react-router-dom'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import SeccionAdquisicion from '../components/SeccionAdquisicion.jsx'
import { navegacionEstudio, useEstudioRx } from '../hooks/useEstudioRx.js'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'
import '../../../laboratorio/pages/area-resultados.css'
import '../../asistente/pages/rayos-x.css'
import './estudio.css'

/** Adquisición: registro técnico e imágenes (como "Capturar resultados" de Laboratorio), con la placa a la vista. */
export default function AdquisicionRayosXPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const { data: detalle, isLoading, isError, error } = useEstudioRx(estudioId)
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacionEstudio(detalle, estudioId, 'Adquisición')} clase="rx-trabajo">
    {isLoading && <p role="status">Cargando estudio…</p>}
    {isError && <p role="alert" className="lab-form-error">{mensajeError(error, 'No se pudo cargar el estudio.')}</p>}
    {detalle && <>
      <header className="lab-area-results-header">
        <p className="lab-eyebrow">ADQUISICIÓN · {detalle.estudio.referencia_estudio}</p>
        <h1>{detalle.estudio.tipo_estudio_nombre}</h1>
        <p>{detalle.paciente.nombre_completo} · {detalle.paciente.edad ?? '—'} / {detalle.paciente.sexo || '—'}{detalle.estudio.detalle?.indicacion_clinica ? ` · ${detalle.estudio.detalle.indicacion_clinica}` : ''}{detalle.estudio.prioridad === 'urgente' ? ' · Urgente' : ''}</p>
      </header>
      <SeccionAdquisicion estudioId={estudioId} detalle={detalle} />
    </>}
  </RayosXLayout>
}
