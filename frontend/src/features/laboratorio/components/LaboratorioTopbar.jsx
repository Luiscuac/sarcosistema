import { Link } from 'react-router-dom'

export default function LaboratorioTopbar({ usuario, onLogout }) {
  return (
    <header className="lab-topbar">
      <Link className="lab-brand" to="/laboratorio" title="Ir a la bandeja de solicitudes">
        <strong>SarcoSistema</strong>
        <span>Laboratorio</span>
      </Link>
      <div className="lab-session">
        <span className="lab-session-user" title={usuario.identificador_acceso}>
          {usuario.identificador_acceso}
        </span>
        <button className="lab-signout" type="button" onClick={onLogout}>Cerrar sesión</button>
      </div>
    </header>
  )
}
