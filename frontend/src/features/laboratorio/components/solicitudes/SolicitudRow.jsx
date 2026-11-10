import { Link } from 'react-router-dom'
import ProgresoSolicitud from './ProgresoSolicitud.jsx'
import { estadoSolicitud } from '../../utils/agruparSolicitudes.js'
import { esperaProlongada, progresoSolicitud, siguienteAccion, tiempoTranscurrido } from '../../utils/bandeja.js'
import './solicitudes-panel.css'

function claseEstado(estudios) {
  if (progresoSolicitud(estudios).completa) return 'publicado'
  return estudios.some((estudio) => ['resultado_en_preparacion', 'publicado'].includes(estudio.estado))
    ? 'resultado_en_preparacion'
    : 'pendiente_muestra'
}

export default function SolicitudRow({ solicitud, ahora }) {
  const accion = siguienteAccion(solicitud)
  const demorada = esperaProlongada(solicitud, ahora)
  const urgente = solicitud.prioridad === 'urgente'

  return (
    <tr className={urgente ? 'lab-table-row lab-table-row--urgent' : 'lab-table-row'}>
      <td>
        <strong>{solicitud.paciente_nombre}</strong>
        <span>{solicitud.referencia}</span>
        <small className={demorada ? 'lab-wait is-long' : 'lab-wait'} title={new Date(solicitud.fecha_solicitud).toLocaleString('es-BO')}>
          {demorada && <span aria-hidden="true">⚠ </span>}Solicitada {tiempoTranscurrido(solicitud.fecha_solicitud, ahora)}
          {demorada && <span className="sr-only"> (espera prolongada)</span>}
        </small>
      </td>
      <td><span className={`lab-status lab-status--${claseEstado(solicitud.estudios)}`}>{estadoSolicitud(solicitud.estudios)}</span></td>
      <td><ProgresoSolicitud estudios={solicitud.estudios} /></td>
      <td>{urgente ? <strong className="lab-priority">Urgente</strong> : 'Programada'}</td>
      <td className="lab-row-action">
        <Link className={`lab-next-action lab-next-action--${accion.tipo}`} to={accion.ruta}>{accion.etiqueta}</Link>
        {accion.tipo !== 'abrir' && <Link className="lab-row-secondary" to={`/laboratorio/solicitudes/${solicitud.id}`}>Ver detalle</Link>}
      </td>
    </tr>
  )
}
