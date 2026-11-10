import './EstudiosSolicitados.css'

export default function EstudiosSolicitados({
  cargando, error, catalogo, busqueda, onBusquedaChange, seleccionados,
  idsSeleccionados, grupos, hayResultados, onToggle,
}) {
  return <section className="lab-form-section">
    <h3>3. Estudios solicitados</h3>
    {cargando && <p className="lab-form-hint">Cargando catálogo…</p>}
    {error && <p className="lab-form-error">No se pudo cargar el catálogo de laboratorio.</p>}
    {!cargando && !error && catalogo.length === 0 && <p className="lab-form-hint">No hay estudios disponibles para registrar. Contacta al administrador del sistema.</p>}

    <div className="lab-selected-studies" aria-live="polite">
      <span className="lab-field-label">{seleccionados.length ? `Seleccionados (${seleccionados.length})` : 'Ningún estudio seleccionado todavía'}</span>
      {seleccionados.length > 0 && <ul>
        {seleccionados.map((estudio) => <li key={estudio.id} className="lab-chip">{estudio.nombre}
          <button type="button" onClick={() => onToggle(estudio.id)} aria-label={`Quitar ${estudio.nombre}`}>×</button>
        </li>)}
      </ul>}
    </div>

    <label className="lab-search-label lab-study-search">Buscar estudio
      <input type="search" value={busqueda} onChange={(evento) => onBusquedaChange(evento.target.value)} placeholder="Nombre de la prueba" />
    </label>
    {grupos.map((grupo) => <div className="lab-study-group" key={grupo.codigo ?? 'sin-categoria'}>
      <h4>{grupo.nombre}</h4>
      <div className="lab-study-options">{grupo.estudios.map((estudio) => <label className="lab-study-option" key={estudio.id}>
        <input type="checkbox" checked={idsSeleccionados.includes(estudio.id)} onChange={() => onToggle(estudio.id)} />
        <span><strong>{estudio.nombre}</strong></span>
      </label>)}</div>
    </div>)}
    {busqueda.trim() && !hayResultados && <p className="lab-form-hint">No hay estudios con ese nombre.</p>}
  </section>
}
