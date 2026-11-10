function MedicoSolicitante({ datos, onChange, medicosQuery, onSeleccionarMedico }) {
  const deEsteCentro = datos.procedencia === 'este_centro'
  if (deEsteCentro && datos.medico_solicitante_id) {
    return <div className="lab-chip-field">
      <span className="lab-field-label">Profesional solicitante</span>
      <span className="lab-chip">{datos.medico_solicitante_nombre}
        <button type="button" onClick={() => onChange('medico_solicitante_nombre', '')} aria-label="Cambiar médico">Cambiar</button>
      </span>
    </div>
  }
  const termino = datos.medico_solicitante_nombre.trim()
  return <div>
    <label>Profesional solicitante
      <input required value={datos.medico_solicitante_nombre} onChange={(e) => onChange('medico_solicitante_nombre', e.target.value)}
        autoComplete="off" placeholder={deEsteCentro ? 'Escribe y elige de la lista' : 'Nombre del profesional'} />
    </label>
    {deEsteCentro && termino.length >= 2 && <>
      {medicosQuery.isFetching && <p className="lab-form-hint">Buscando médicos…</p>}
      {medicosQuery.isError && <p className="lab-form-error">No se pudo buscar médicos.</p>}
      {medicosQuery.data?.map((medico) => <button type="button" className="lab-patient-option" key={medico.id} onClick={() => onSeleccionarMedico(medico)}>{medico.nombre}</button>)}
      {medicosQuery.isSuccess && !medicosQuery.isFetching && medicosQuery.data.length === 0 && <p className="lab-form-hint">No se encontró un médico activo con ese nombre.</p>}
    </>}
  </div>
}

export default function DatosPedido({ datos, onChange, medicosQuery, onSeleccionarMedico }) {
  return <section className="lab-form-section">
    <h3>2. Datos del pedido</h3>
    <div className="lab-form-grid">
      <label>Procedencia<select value={datos.procedencia} onChange={(e) => onChange('procedencia', e.target.value)}><option value="este_centro">Sarcobamba</option><option value="otro_centro">De otro centro</option></select></label>
      <label>Prioridad<select value={datos.prioridad} onChange={(e) => onChange('prioridad', e.target.value)}><option value="sin_prioridad">Programada / sin prioridad</option><option value="urgente">Urgente</option></select></label>
      {datos.procedencia === 'otro_centro' && <label className="lab-full-field">Nombre del otro centro<input required value={datos.establecimiento_solicitante_nombre} onChange={(e) => onChange('establecimiento_solicitante_nombre', e.target.value)} placeholder="Centro que solicitó los estudios" /></label>}
      <MedicoSolicitante datos={datos} onChange={onChange} medicosQuery={medicosQuery} onSeleccionarMedico={onSeleccionarMedico} />
      <label>Fecha de solicitud<input required type="date" max={new Date().toLocaleDateString('en-CA')} value={datos.fecha_solicitud} onChange={(e) => onChange('fecha_solicitud', e.target.value)} /></label>
      <label>N.º de formulario D-8 (opcional)<input value={datos.referencia_papel_formulario} onChange={(e) => onChange('referencia_papel_formulario', e.target.value)} placeholder="Ej.: 0391521" /></label>
      <label>Diagnóstico principal (opcional)<input value={datos.diagnostico_principal} onChange={(e) => onChange('diagnostico_principal', e.target.value)} /></label>
    </div>
  </section>
}
