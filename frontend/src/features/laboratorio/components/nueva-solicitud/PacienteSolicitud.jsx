import { describirEdad } from '../../../../shared/utils/edad.js'
import { formatearFecha } from '../../../../shared/utils/formatearFecha.js'
import { nombreSexo, SEXOS, TIPOS_DOCUMENTO } from '../../utils/catalogos.js'
import './PacienteSolicitud.css'

function detallePaciente(paciente) {
  return [
    paciente.numero_documento ? `Doc. ${paciente.numero_documento}` : 'Sin documento',
    paciente.fecha_nacimiento && `${describirEdad(paciente.fecha_nacimiento)} (${formatearFecha(paciente.fecha_nacimiento)})`,
    paciente.sexo && nombreSexo(paciente.sexo),
    paciente.historia_clinica && `HC ${paciente.historia_clinica}`,
    paciente.codigo_externo && `Código interno ${paciente.codigo_externo}`,
  ].filter(Boolean).join(' · ')
}

function FormularioPaciente({ datos, pendiente, onChange, onCancelar, onGuardar }) {
  return <div className="lab-inline-patient-form">
    <div className="lab-form-grid">
      <label className="lab-full-field">Nombre completo<input required minLength="2" autoFocus value={datos.nombre_completo} onChange={(e) => onChange('nombre_completo', e.target.value)} /></label>
      <label>Fecha de nacimiento
        <input required type="date" max={new Date().toLocaleDateString('en-CA')} value={datos.fecha_nacimiento} onChange={(e) => onChange('fecha_nacimiento', e.target.value)} />
        {datos.fecha_nacimiento && <small>{describirEdad(datos.fecha_nacimiento)}</small>}
      </label>
      <label>Sexo registrado<select value={datos.sexo} onChange={(e) => onChange('sexo', e.target.value)}>
        {SEXOS.map(({ codigo, nombre }) => <option key={codigo} value={codigo}>{nombre}</option>)}
      </select></label>
      <label className="lab-checkbox-label lab-full-field"><input type="checkbox" checked={datos.sin_documento} onChange={(e) => onChange('sin_documento', e.target.checked)} /> Persona sin documento</label>
      {!datos.sin_documento && <>
        <label>Tipo de documento<select required value={datos.tipo_documento} onChange={(e) => onChange('tipo_documento', e.target.value)}>
          {TIPOS_DOCUMENTO.map((tipo) => <option key={tipo} value={tipo}>{tipo}</option>)}
        </select></label>
        <label>Número de documento<input required value={datos.numero_documento} onChange={(e) => onChange('numero_documento', e.target.value)} /></label>
      </>}
      <label>N.º de historia clínica (opcional)<input value={datos.historia_clinica} onChange={(e) => onChange('historia_clinica', e.target.value)} placeholder="Si figura en el registro" maxLength="80" /></label>
      <label>Código interno de laboratorio (opcional)<input value={datos.codigo_externo} onChange={(e) => onChange('codigo_externo', e.target.value)} maxLength="80" /></label>
      <label>Teléfono (opcional)<input type="tel" value={datos.telefono} onChange={(e) => onChange('telefono', e.target.value)} maxLength="40" /></label>
    </div>
    <div className="lab-inline-actions">
      <button type="button" onClick={onCancelar}>Volver a buscar</button>
      <button className="primary-button" type="button" disabled={pendiente} onClick={onGuardar}>{pendiente ? 'Guardando…' : 'Guardar paciente'}</button>
    </div>
  </div>
}

export default function PacienteSolicitud({
  paciente, nuevoPaciente, datosPaciente, termino, buscando, pacientesQuery, crearPacientePendiente,
  onSelect, onTerminoChange, onStartCreate, onCancelCreate, onPacienteChange, onCreatePaciente,
}) {
  const resultados = pacientesQuery.data ?? []
  const sinResultados = termino.trim().length >= 2 && !buscando && pacientesQuery.isSuccess && resultados.length === 0

  return <section className="lab-form-section">
    <h3>1. Paciente</h3>
    {paciente ? <div className="lab-selected-patient">
      <div><strong>{paciente.nombre_completo}</strong><span>{detallePaciente(paciente)}</span></div>
      <button type="button" onClick={() => onSelect(null)}>Cambiar</button>
    </div> : nuevoPaciente ? <FormularioPaciente datos={datosPaciente} pendiente={crearPacientePendiente}
      onChange={onPacienteChange} onCancelar={onCancelCreate} onGuardar={onCreatePaciente} />
      : <>
        <label className="lab-search-label">Buscar por nombre, documento, historia clínica o código
          <input autoFocus type="search" value={termino} onChange={(e) => onTerminoChange(e.target.value)} placeholder="Escribe al menos 2 caracteres" />
        </label>
        {termino.trim().length >= 2 && buscando && <p className="lab-form-hint">Buscando pacientes…</p>}
        {pacientesQuery.isError && <p className="lab-form-error">No se pudo buscar. Comprueba la conexión e inténtalo de nuevo.</p>}
        {resultados.map((item) => <button className="lab-patient-option" type="button" key={item.id} onClick={() => onSelect(item)}>
          <strong>{item.nombre_completo}</strong><span>{detallePaciente(item)}</span>
        </button>)}
        {sinResultados && <p className="lab-form-hint">No se encontró el paciente. Revisa la escritura o regístralo con los datos mínimos.</p>}
        <button className="lab-text-button" type="button" onClick={onStartCreate}>+ Registrar paciente nuevo</button>
      </>}
  </section>
}
