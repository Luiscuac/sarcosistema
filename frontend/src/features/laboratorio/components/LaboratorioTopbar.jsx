export default function LaboratorioTopbar({ usuario }) {
  return (
    <header className="lab-topbar">
      <span>UNIDAD DE ANÁLISIS CLÍNICO</span>
      <div className="lab-session">
        <span className="lab-session-status"><span aria-hidden="true" /> Sesión activa</span>
        <span className="lab-session-user" title={usuario.identificador_acceso}>
          {usuario.identificador_acceso}
        </span>
      </div>
    </header>
  )
}
