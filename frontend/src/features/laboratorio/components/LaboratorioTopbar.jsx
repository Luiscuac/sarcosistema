export default function LaboratorioTopbar({ usuario, onLogout }) {
  return (
    <header className="lab-topbar">
      <div className="lab-brand">
        <strong>SarcoSistema</strong>
        <span>Laboratorio</span>
      </div>
      <div className="lab-session">
        <span className="lab-session-user" title={usuario.identificador_acceso}>
          {usuario.identificador_acceso}
        </span>
        <button className="lab-signout" type="button" onClick={onLogout}>Cerrar sesión</button>
      </div>
    </header>
  )
}
