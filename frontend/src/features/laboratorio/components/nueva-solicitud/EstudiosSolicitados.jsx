import './EstudiosSolicitados.css'

export default function EstudiosSolicitados({
  cargando, error, catalogo, busqueda, onBusquedaChange, cantidadSeleccionada,
  idsSeleccionados, grupos, estudiosVisibles, onToggle,
}) {
  return <section className="lab-form-section">
    <h3>3. Estudios solicitados</h3>
    {cargando && <p className="lab-form-hint">Cargando catálogo…</p>}
    {error && <p className="lab-form-error">No se pudo cargar el catálogo de laboratorio.</p>}
    {!cargando && !error && catalogo.length === 0 && <p className="lab-form-hint">No hay estudios disponibles para registrar. Contacta al administrador del sistema.</p>}
    <p className="lab-form-hint">Selecciona las pruebas indicadas en el pedido. Cada una quedará asociada a esta solicitud.</p>
    <label className="lab-search-label lab-study-search">Buscar estudio
      <input type="search" value={busqueda} onChange={(event) => onBusquedaChange(event.target.value)} placeholder="Nombre de la prueba" />
    </label>
    <p className="lab-form-hint" role="status">{cantidadSeleccionada} {cantidadSeleccionada === 1 ? 'estudio seleccionado' : 'estudios seleccionados'}</p>
    {grupos.map((grupo) => <div className="lab-study-group" key={grupo.codigo ?? 'sin-categoria'}>
      <h4>{grupo.nombre}</h4>
      <div className="lab-study-options">{grupo.estudios.map((estudio) => <label className="lab-study-option" key={estudio.id}>
        <input type="checkbox" checked={idsSeleccionados.includes(estudio.id)} onChange={() => onToggle(estudio.id)} />
        <span><strong>{estudio.nombre}</strong></span>
      </label>)}</div>
    </div>)}
    {busqueda.trim() && !estudiosVisibles.length && <p className="lab-form-hint">No hay estudios con ese nombre.</p>}
  </section>
}
