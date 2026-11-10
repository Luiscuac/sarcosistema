import { progresoSolicitud } from '../../utils/bandeja.js'

export default function ProgresoSolicitud({ estudios }) {
  const { total, finalizados } = progresoSolicitud(estudios)
  const porcentaje = total ? Math.round((finalizados / total) * 100) : 0
  return (
    <div className="lab-request-progress">
      <span>{finalizados}/{total} {total === 1 ? 'estudio listo' : 'estudios listos'}</span>
      <div className="lab-progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={finalizados}
        aria-label={`${finalizados} de ${total} estudios publicados o cerrados`}>
        <span style={{ width: `${porcentaje}%` }} />
      </div>
    </div>
  )
}
