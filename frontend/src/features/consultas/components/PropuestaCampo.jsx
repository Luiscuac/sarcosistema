import { useState } from 'react'
import { necesitaVerificacion } from '../utils/sugerencias.js'

function estadoVisible(item) {
  if (item.ambiguo) return 'Ambiguo · completar manualmente'
  if (necesitaVerificacion(item)) return 'Revisar antes de aplicar'
  return 'Lista para aplicar'
}

/** Propuesta de la IA para un campo: valor editable, lo que se dijo y avisos a verificar. */
export default function PropuestaCampo({ item, etiqueta, valorActual, bloqueada, onCambiarValor, onAceptar, onRechazar }) {
  const [verificado, setVerificado] = useState(false)
  const conAlertas = necesitaVerificacion(item)
  const puedeAceptar = !item.ambiguo && !bloqueada && (!conAlertas || verificado)

  return <div className={`med-suggestion${conAlertas || item.ambiguo ? ' med-suggestion--revisar' : ''}`}>
    <div className="med-ai-title"><strong>{etiqueta}</strong><span>{estadoVisible(item)}</span></div>
    {Boolean(valorActual) && <p className="med-ai-current">Valor actual: {String(valorActual)}</p>}
    <label className="med-ai-text">Valor propuesto{typeof item.valor === 'number'
      ? <input type="number" step="any" disabled={item.ambiguo} value={item.valor} onChange={e => onCambiarValor(e.target.value)} />
      : <textarea rows={2} disabled={item.ambiguo} value={item.valor} onChange={e => onCambiarValor(e.target.value)} />}</label>
    <blockquote><strong>Lo que se dijo:</strong> «{item.evidencia}»</blockquote>
    {item.alertas?.length > 0 && <ul className="med-ai-alerts" aria-label="Avisos para revisar">
      {item.alertas.map(alerta => <li key={alerta}>{alerta}</li>)}
    </ul>}
    {conAlertas && !item.ambiguo && <label className="med-ai-verify">
      <input type="checkbox" checked={verificado} onChange={e => setVerificado(e.target.checked)} />
      Revisé los avisos y el valor es correcto (puedo editarlo arriba).
    </label>}
    <div className="med-ai-actions">
      <button type="button" disabled={!puedeAceptar} onClick={onAceptar}>Aceptar este campo</button>
      <button type="button" onClick={onRechazar}>Rechazar</button>
    </div>
  </div>
}
