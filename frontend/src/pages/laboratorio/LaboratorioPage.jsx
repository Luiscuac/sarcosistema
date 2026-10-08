import './laboratorio.css'

export default function LaboratorioPage({ usuario, logout }) {
  return (
    <main className="lab-page">
      <aside className="lab-sidebar">
        <div className="lab-sidebar-heading">
          <strong>SarcoSistema</strong>
          <span>LABORATORIO</span>
        </div>
        <nav className="lab-nav" aria-label="Módulo de laboratorio">
          <span className="lab-nav-item lab-nav-item--active" aria-current="page">Solicitudes</span>
          <span className="lab-nav-item lab-nav-item--inactive">Pacientes</span>
          <span className="lab-nav-item lab-nav-item--inactive">Formatos</span>
          <span className="lab-nav-item lab-nav-item--inactive">Referencias</span>
        </nav>
        <button className="lab-signout" onClick={logout}>Cerrar sesión</button>
      </aside>
      <div className="lab-main">
        <header className="lab-topbar">
          <span>UNIDAD DE ANÁLISIS CLÍNICO</span>
          <div className="lab-session">
            <span className="lab-session-status"><span aria-hidden="true" /> Sesión activa</span>
            <span className="lab-session-user" title={usuario.identificador_acceso}>
              {usuario.identificador_acceso}
            </span>
          </div>
        </header>
        <section className="lab-content">
          <div className="lab-title-row">
            <div>
              <p className="lab-eyebrow">LABORATORIO</p>
              <h1>Solicitudes de laboratorio</h1>
              <p className="lab-intro">Seguimiento de estudios y resultados asociados a cada paciente.</p>
            </div>
            <span className="lab-view-label">Vista inicial</span>
          </div>

          <div className="lab-summary" aria-label="Indicadores de laboratorio">
            <div className="lab-summary-card"><span>Solicitudes de hoy</span><strong>—</strong><small>Datos pendientes</small></div>
            <div className="lab-summary-card"><span>Pendientes de validación</span><strong>—</strong><small>Datos pendientes</small></div>
            <div className="lab-summary-card"><span>En análisis</span><strong>—</strong><small>Datos pendientes</small></div>
            <div className="lab-summary-card"><span>Publicadas</span><strong>—</strong><small>Datos pendientes</small></div>
          </div>

          <div className="lab-list-panel">
            <div className="lab-list-toolbar">
              <div>
                <h2>Buscar solicitudes</h2>
                <p>Consulta por paciente o número de solicitud.</p>
              </div>
              <span className="lab-pending-tag">Consulta pendiente de integración</span>
            </div>
            <input className="lab-search" type="search" placeholder="Buscar paciente o solicitud" disabled
              aria-label="Buscar paciente o solicitud; función aún no disponible" />
            <div className="lab-table-wrap">
              <table className="lab-table">
                <caption className="sr-only">Solicitudes de laboratorio</caption>
                <thead>
                  <tr><th>Solicitud / paciente</th><th>Estado</th><th>Exámenes</th><th>Acciones</th></tr>
                </thead>
                <tbody>
                  <tr><td className="lab-empty" colSpan="4">
                    <strong>Las solicitudes aún no están disponibles en esta vista.</strong>
                    <span>El acceso al módulo funciona; la consulta de solicitudes se añadirá en el siguiente incremento.</span>
                  </td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="lab-actions">
            <button className="primary-button" type="button" disabled>Nueva solicitud</button>
            <span>Las acciones de laboratorio estarán disponibles cuando se conecte este flujo.</span>
          </div>
        </section>
      </div>
    </main>
  )
}
