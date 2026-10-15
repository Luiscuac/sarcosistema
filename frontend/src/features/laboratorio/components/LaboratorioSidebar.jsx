export default function LaboratorioSidebar({ onLogout }) {
  return (
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
      <button className="lab-signout" onClick={onLogout}>Cerrar sesión</button>
    </aside>
  )
}
