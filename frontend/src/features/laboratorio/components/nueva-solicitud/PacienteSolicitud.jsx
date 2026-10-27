import './PacienteSolicitud.css'

export default function PacienteSolicitud({
  paciente, nuevoPaciente, datosPaciente, termino, pacientesQuery, crearPacientePendiente,
  onSelect, onTerminoChange, onStartCreate, onCancelCreate, onPacienteChange, onCreatePaciente,
}) {
  return <section className="lab-form-section">
    <h3>1. Paciente</h3>
    {paciente ? <div className="lab-selected-patient">
      <div><strong>{paciente.nombre_completo}</strong><span>{paciente.codigo_paciente} · {paciente.numero_documento || 'Sin documento'}{paciente.historia_clinica ? ` · HC ${paciente.historia_clinica}` : ''}</span></div>
      <button type="button" onClick={() => onSelect(null)}>Cambiar</button>
    </div> : nuevoPaciente ? <div className="lab-inline-patient-form">
      <div className="lab-form-grid">
        <label>Nombre completo<input required minLength="2" value={datosPaciente.nombre_completo} onChange={(e) => onPacienteChange('nombre_completo', e.target.value)} /></label>
        <label>Fecha de nacimiento<input required type="date" value={datosPaciente.fecha_nacimiento} onChange={(e) => onPacienteChange('fecha_nacimiento', e.target.value)} /></label>
        <label>Sexo registrado<select value={datosPaciente.sexo} onChange={(e) => onPacienteChange('sexo', e.target.value)}><option value="no_especificado">No especificado</option><option value="F">F</option><option value="M">M</option><option value="otro">Otro</option></select></label>
        <label>N.º de historia clínica<input value={datosPaciente.historia_clinica} onChange={(e) => onPacienteChange('historia_clinica', e.target.value)} placeholder="Si figura en el registro" maxLength="80" /></label>
        <label>Código externo del hospital<input value={datosPaciente.codigo_externo} onChange={(e) => onPacienteChange('codigo_externo', e.target.value)} placeholder="Si figura en el registro" maxLength="80" /></label>
        <label className="lab-checkbox-label"><input type="checkbox" checked={datosPaciente.sin_documento} onChange={(e) => onPacienteChange('sin_documento', e.target.checked)} /> Persona sin documento</label>
        {!datosPaciente.sin_documento && <>
          <label>Tipo de documento<input required value={datosPaciente.tipo_documento} onChange={(e) => onPacienteChange('tipo_documento', e.target.value)} /></label>
          <label>Número de documento<input required value={datosPaciente.numero_documento} onChange={(e) => onPacienteChange('numero_documento', e.target.value)} /></label>
        </>}
      </div>
      <div className="lab-inline-actions">
        <button type="button" onClick={onCancelCreate}>Cancelar</button>
        <button className="primary-button" type="button" disabled={crearPacientePendiente} onClick={onCreatePaciente}>{crearPacientePendiente ? 'Guardando…' : 'Guardar paciente'}</button>
      </div>
    </div> : <>
      <label className="lab-search-label">Buscar por nombre, documento, historia clínica o código
        <input autoFocus type="search" value={termino} onChange={(e) => onTerminoChange(e.target.value)} placeholder="Escribe al menos 2 caracteres" />
      </label>
      {pacientesQuery.isLoading && <p className="lab-form-hint">Buscando pacientes…</p>}
      {pacientesQuery.isError && <p className="lab-form-error">No se pudo buscar. Comprueba la conexión e inténtalo de nuevo.</p>}
      {(pacientesQuery.data ?? []).map((item) => <button className="lab-patient-option" type="button" key={item.id} onClick={() => onSelect(item)}>
        <strong>{item.nombre_completo}</strong><span>{item.codigo_paciente} · {item.numero_documento || 'Sin documento'} · {item.fecha_nacimiento}{item.historia_clinica ? ` · HC ${item.historia_clinica}` : ''}{item.codigo_externo ? ` · Código ${item.codigo_externo}` : ''}</span>
      </button>)}
      {termino.trim().length >= 2 && pacientesQuery.data?.length === 0 && <p className="lab-form-hint">No se encontró el paciente. Puedes registrar una identificación mínima.</p>}
      <button className="lab-text-button" type="button" onClick={onStartCreate}>Registrar paciente si no existe</button>
    </>}
  </section>
}
