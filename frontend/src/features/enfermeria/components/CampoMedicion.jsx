import { useId } from 'react'
import { MEDICIONES, PRESION, avisoDeCampo, errorDeCampo } from '../utils/signosVitales.js'
import '../pages/enfermeria.css'

/** Enter pasa al siguiente campo del formulario (en los cuadros de texto sigue siendo salto de línea). */
export function pasarAlSiguiente(evento) {
  if (evento.key !== 'Enter' || evento.target.tagName === 'TEXTAREA') return
  evento.preventDefault()
  const campos = [...evento.currentTarget.querySelectorAll('[data-campo-admision]:not(:disabled)')]
  campos[campos.indexOf(evento.target) + 1]?.focus()
}

/**
 * Medición con unidad visible, teclado numérico, error en vivo (límites del backend) y aviso
 * de valor fuera de lo habitual. La comparten enfermería y la consulta médica.
 */
export default function CampoMedicion({ campo, valor, edad, deshabilitado, onCambiar, insignia }) {
  const ayudaId = useId()
  const definicion = campo === 'presion' ? PRESION : MEDICIONES[campo]
  const error = errorDeCampo(campo, valor)
  const aviso = avisoDeCampo(campo, valor, edad)
  const clase = ['enf-measure', error && 'is-invalid', aviso && `is-${aviso.nivel}`].filter(Boolean).join(' ')
  return <label className={clase}>
    <span>{definicion.etiqueta}{insignia}</span>
    <span className="enf-measure-input">
      <input data-campo-admision type="text" autoComplete="off" disabled={deshabilitado}
        inputMode={campo === 'presion' ? 'text' : 'decimal'} value={valor}
        placeholder={campo === 'presion' ? PRESION.ejemplo : '—'}
        aria-invalid={Boolean(error)} aria-describedby={error || aviso ? ayudaId : undefined}
        onChange={(evento) => onCambiar(campo, evento.target.value)} />
      <small>{definicion.unidad}</small>
    </span>
    {(error || aviso) && <small id={ayudaId} className="enf-measure-note">{error ?? aviso.texto}</small>}
  </label>
}
