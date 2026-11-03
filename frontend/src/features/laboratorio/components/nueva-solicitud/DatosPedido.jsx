export default function DatosPedido({ datos, onChange }) {
  return <section className="lab-form-section">
    <h3>2. Datos del pedido</h3>
    <div className="lab-form-grid">
      <label>N.º de formulario D-8 (opcional)<input value={datos.referencia_papel_formulario} onChange={(e) => onChange('referencia_papel_formulario', e.target.value)} placeholder="Ej.: 0391521" /></label>
      <label>Fecha de solicitud<input required type="date" value={datos.fecha_solicitud} onChange={(e) => onChange('fecha_solicitud', e.target.value)} /></label>
      <label>Procedencia<select value={datos.procedencia} onChange={(e) => onChange('procedencia', e.target.value)}><option value="este_centro">Sarcobamba</option><option value="otro_centro">De otro centro</option></select></label>
      {datos.procedencia === 'otro_centro' && <label>Nombre del otro centro<input required value={datos.establecimiento_solicitante_nombre} onChange={(e) => onChange('establecimiento_solicitante_nombre', e.target.value)} placeholder="Centro que solicitó los estudios" /></label>}
      <label>Profesional solicitante<input required value={datos.medico_solicitante_nombre} onChange={(e) => onChange('medico_solicitante_nombre', e.target.value)} /></label>
      <label>Prioridad<select value={datos.prioridad} onChange={(e) => onChange('prioridad', e.target.value)}><option value="sin_prioridad">Programada / sin prioridad</option><option value="urgente">Urgente</option></select></label>
      <label className="lab-full-field">Diagnóstico principal<input value={datos.diagnostico_principal} onChange={(e) => onChange('diagnostico_principal', e.target.value)} placeholder="Opcional" /></label>
    </div>
  </section>
}
