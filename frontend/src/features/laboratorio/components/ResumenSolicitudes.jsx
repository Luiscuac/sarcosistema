const indicadores = [
  'Solicitudes de hoy',
  'Pendientes de validación',
  'En análisis',
  'Publicadas',
]

export default function ResumenSolicitudes() {
  return (
    <div className="lab-summary" aria-label="Indicadores de laboratorio">
      {indicadores.map((indicador) => (
        <div className="lab-summary-card" key={indicador}>
          <span>{indicador}</span><strong>—</strong><small>Datos pendientes</small>
        </div>
      ))}
    </div>
  )
}
