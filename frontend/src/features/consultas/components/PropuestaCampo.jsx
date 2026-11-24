import { useState } from 'react'
import { necesitaVerificacion } from '../utils/sugerencias.js'

function estadoVisible(item) {
  if (item.ambiguo) return 'Ambiguo · completar manualmente'
  if (necesitaVerificacion(item)) return 'Revisar antes de aplicar'
  return 'Lista para aplicar'
}

/** Propuesta de la IA para un campo: editable, con evidencia y avisos para revisar. */
export default function PropuestaCampo({ item, etiqueta, valorActual, bloqueada, onCambiarValor, onAceptar, onRechazar }) {
  const [verificado, setVerificado] = useState(false)
  const conAlertas = necesitaVerificacion(item)
  const puedeAceptar = !item.ambiguo && !bloqueada && (!conAlertas || verificado)

  return <article className={`enf-ai-proposal${conAlertas || item.ambiguo ? ' med-suggestion--revisar' : ''}`}>
    <header className="enf-ai-proposal-header">
      <strong>{etiqueta}</strong><span className="enf-ai-proposal-status">{estadoVisible(item)}</span>
    </header>
    {Boolean(valorActual) && <p className="med-ai-current">Valor actual: {String(valorActual)}</p>}
    <label className="enf-ai-proposal-value med-ai-value-editable"><span>Valor propuesto</span>{typeof item.valor === 'number'
      ? <input type="number" step="any" disabled={item.ambiguo} value={item.valor} onChange={e => onCambiarValor(e.target.value)} />
      : <textarea rows={2} disabled={item.ambiguo} value={item.valor} onChange={e => onCambiarValor(e.target.value)} />}</label>
    <blockquote className="enf-ai-proposal-evidence"><span>Lo que se dijo</span><q>{item.evidencia}</q></blockquote>
    {item.alertas?.length > 0 && <ul className="enf-ai-proposal-alerts" aria-label="Avisos para revisar">
      {item.alertas.map(alerta => <li key={alerta}>{alerta}</li>)}
    </ul>}
    {conAlertas && !item.ambiguo && <label className="med-ai-verify">
      <input type="checkbox" checked={verificado} onChange={e => setVerificado(e.target.checked)} />
      Revisé los avisos y el valor es correcto (puedo editarlo arriba).
    </label>}
    <div className="enf-ai-proposal-actions">
      <button type="button" className="enf-ai-accept" disabled={!puedeAceptar} onClick={onAceptar}>Aceptar este campo</button>
      <button type="button" className="enf-ai-reject" onClick={onRechazar}>Rechazar</button>
    </div>
  </article>
}
