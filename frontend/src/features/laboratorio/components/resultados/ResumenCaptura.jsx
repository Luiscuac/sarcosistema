import './captura.css'

/** Barra de avance y motivo por el que todavía no se puede publicar. */
export default function ResumenCaptura({ resumen, motivoBloqueo }) {
  const porcentaje = resumen.total ? Math.round((resumen.completos / resumen.total) * 100) : 0
  return (
    <div className="lab-capture-summary" aria-live="polite">
      <div className="lab-capture-progress">
        <span><strong>{resumen.completos} de {resumen.total}</strong> campos completos</span>
        <div className="lab-progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={resumen.total} aria-valuenow={resumen.completos} aria-label="Campos completos">
          <span style={{ width: `${porcentaje}%` }} />
        </div>
      </div>
      {resumen.fueraDeRango.length > 0 && <p className="lab-capture-warning">
        {resumen.fueraDeRango.length === 1 ? '1 valor está' : `${resumen.fueraDeRango.length} valores están`} fuera del rango de referencia. No es un error: confírmalo antes de publicar.
      </p>}
      {motivoBloqueo && <p className="lab-capture-blocked">{motivoBloqueo}</p>}
    </div>
  )
}
