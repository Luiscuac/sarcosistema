import { useExamenes } from '../hooks/useExamenes.js'
import { agruparSolicitudes } from '../utils/agruparSolicitudes.js'

export default function ResumenSolicitudes() {
  const { data: estudios = [], isLoading, isError } = useExamenes()
  const solicitudes = agruparSolicitudes(estudios)
  const indicadores = [
    { nombre: 'Solicitudes pendientes', valor: solicitudes.length },
    { nombre: 'Con muestras por recibir', valor: solicitudes.filter((s) => s.estudios.some((e) => e.estado === 'pendiente_muestra')).length },
    { nombre: 'Con resultados en preparación', valor: solicitudes.filter((s) => s.estudios.some((e) => e.estado === 'resultado_en_preparacion')).length },
    { nombre: 'Solicitudes urgentes', valor: solicitudes.filter((s) => s.prioridad === 'urgente').length },
  ]

  return (
    <div className="lab-summary" aria-label="Indicadores de laboratorio">
      {indicadores.map((indicador) => (
        <div className="lab-summary-card" key={indicador.nombre}>
          <span>{indicador.nombre}</span>
          <strong>{isLoading ? '…' : isError ? '—' : indicador.valor}</strong>
          <small>{isError ? 'No disponible' : 'Según la bandeja actual'}</small>
        </div>
      ))}
    </div>
  )
}
