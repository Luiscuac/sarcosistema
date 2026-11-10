import { Link } from 'react-router-dom'
import { estadoSolicitud } from '../../utils/agruparSolicitudes.js'
import './solicitudes-panel.css'

export default function SolicitudRow({ solicitud }) {
  const finalizada = solicitud.estudios.every((estudio) => ['publicado', 'no_realizado'].includes(estudio.estado))
  const claseEstado = finalizada
    ? 'publicado'
    : solicitud.estudios.some((estudio) => estudio.estado === 'resultado_en_preparacion' || estudio.estado === 'publicado')
      ? 'resultado_en_preparacion'
      : 'pendiente_muestra'
  const claseFila = solicitud.prioridad === 'urgente'
    ? 'lab-table-row lab-table-row--urgent'
    : 'lab-table-row'

  return (
    <tr className={claseFila}>
      <td><strong>{solicitud.referencia}</strong><span>{solicitud.paciente_nombre}</span><small>{new Date(solicitud.fecha_solicitud).toLocaleString('es-BO')}</small></td>
      <td><span className={`lab-status lab-status--${claseEstado}`}>{estadoSolicitud(solicitud.estudios)}</span></td>
      <td>{solicitud.estudios.length} {solicitud.estudios.length === 1 ? 'estudio' : 'estudios'}</td>
      <td>{solicitud.prioridad === 'urgente' ? <strong className="lab-priority">Urgente</strong> : 'Normal'}</td>
      <td className="lab-row-action"><Link to={`/laboratorio/solicitudes/${solicitud.id}`}>Abrir solicitud</Link></td>
    </tr>
  )
}
