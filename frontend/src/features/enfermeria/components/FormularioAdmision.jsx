import { useId } from 'react'
import {
  GRUPOS, MEDICIONES, PRESION, TEXTOS, avisoDeCampo, calcularImc, errorDeCampo,
} from '../utils/signosVitales.js'

/** Enter pasa al siguiente campo del formulario (en los cuadros de texto sigue siendo salto de línea). */
function pasarAlSiguiente(evento) {
  if (evento.key !== 'Enter' || evento.target.tagName === 'TEXTAREA') return
  evento.preventDefault()
  const campos = [...evento.currentTarget.querySelectorAll('[data-campo-admision]:not(:disabled)')]
  campos[campos.indexOf(evento.target) + 1]?.focus()
}

function CampoMedicion({ campo, valor, edad, deshabilitado, onCambiar }) {
  const ayudaId = useId()
  const definicion = campo === 'presion' ? PRESION : MEDICIONES[campo]
  const error = errorDeCampo(campo, valor)
  const aviso = avisoDeCampo(campo, valor, edad)
  const clase = ['enf-measure', error && 'is-invalid', aviso && `is-${aviso.nivel}`].filter(Boolean).join(' ')
  return <label className={clase}>
    <span>{definicion.etiqueta}</span>
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

function EscalaDolor({ valor, deshabilitado, onCambiar }) {
  const aviso = avisoDeCampo('dolor_escala', valor)
  return <fieldset className="enf-pain">
    <legend>Dolor <small>escala de 0 (sin dolor) a 10 (máximo)</small></legend>
    <div role="radiogroup" aria-label="Dolor de 0 a 10">
      {Array.from({ length: 11 }, (_, nivel) => String(nivel)).map((nivel) => <button key={nivel} type="button"
        role="radio" aria-checked={valor === nivel} disabled={deshabilitado}
        className={`enf-pain-option enf-pain-${Number(nivel) >= 7 ? 'high' : Number(nivel) >= 4 ? 'mid' : 'low'}${valor === nivel ? ' is-selected' : ''}`}
        onClick={() => onCambiar('dolor_escala', valor === nivel ? '' : nivel)}>{nivel}</button>)}
      {valor !== '' && <button type="button" className="enf-pain-clear" disabled={deshabilitado} onClick={() => onCambiar('dolor_escala', '')}>Sin registrar</button>}
    </div>
    {aviso && <small className="enf-measure-note is-high">{aviso.texto}</small>}
  </fieldset>
}

/**
 * Admisión de enfermería: primero lo que se mide, después lo referido.
 * Los valores fuera de lo habitual se resaltan pero no bloquean; los inválidos sí.
 */
export default function FormularioAdmision({ form, edad, editando, ocupado, error, hayErrores, onCambiar, onGuardar, onCancelarEdicion }) {
  const imc = calcularImc(form.peso_kg, form.talla_cm)
  return <form className="enf-form" onKeyDown={pasarAlSiguiente} onSubmit={(evento) => { evento.preventDefault(); onGuardar(false) }} noValidate>
    {GRUPOS.map(({ titulo, campos }) => <fieldset key={titulo} className="enf-group">
      <legend>{titulo}</legend>
      <div className="enf-measurements">
        {campos.map((campo) => <CampoMedicion key={campo} campo={campo} valor={form[campo]} edad={edad} deshabilitado={ocupado} onCambiar={onCambiar} />)}
        {titulo === 'Antropometría' && <div className="enf-measure enf-imc" aria-live="polite">
          <span>IMC (calculado)</span><strong>{imc === null ? '—' : String(imc).replace('.', ',')}</strong>
        </div>}
      </div>
    </fieldset>)}
    <EscalaDolor valor={form.dolor_escala} deshabilitado={ocupado} onCambiar={onCambiar} />
    <fieldset className="enf-group">
      <legend>Referido por el paciente y observaciones</legend>
      {TEXTOS.map(([campo, etiqueta]) => <label key={campo} className="enf-field">{etiqueta}
        <textarea data-campo-admision rows={2} value={form[campo]} disabled={ocupado} onChange={(evento) => onCambiar(campo, evento.target.value)} />
      </label>)}
    </fieldset>
    {edad !== null && edad < 18 && <p className="enf-message">Paciente menor de edad: FC, FR y presión no se comparan con referencias de adulto.</p>}
    {error && <p role="alert" className="enf-error">{error}</p>}
    <div className="enf-actions">
      {editando && <button type="button" onClick={onCancelarEdicion} disabled={ocupado}>Cancelar edición</button>}
      <button type="submit" disabled={ocupado || hayErrores}>{ocupado ? 'Guardando…' : editando ? 'Guardar cambios' : 'Guardar borrador'}</button>
      <button type="button" className="primary-button" disabled={ocupado || hayErrores} onClick={() => onGuardar(true)}>Guardar y publicar…</button>
    </div>
  </form>
}
