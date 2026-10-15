import { Link } from 'react-router-dom'
import './IaSidebar.css'

export default function IaSidebar({ onLogout }) {
  return (
    <aside className="ia-sidebar">
      <div className="ia-sidebar-heading">
        <strong>SarcoSistema</strong><span>ASISTENCIA EXPERIMENTAL</span>
      </div>
      <nav className="ia-nav" aria-label="Módulo de asistencia">
        <Link className="ia-nav-item ia-nav-item--inactive" to="/inicio">Inicio</Link>
        <span className="ia-nav-item ia-nav-item--active" aria-current="page">Transcripción</span>
      </nav>
      <button className="ia-signout" onClick={onLogout}>Cerrar sesión</button>
    </aside>
  )
}
