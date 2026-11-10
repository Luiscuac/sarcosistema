export default function LaboratorioTopbar({ usuario, titulo = 'UNIDAD DE ANÁLISIS CLÍNICO' }) {
  return (
    <header className="lab-topbar">
      <span>{titulo}</span>
      <div className="lab-session">
        <span className="lab-session-status"><span aria-hidden="true" /> Sesión activa</span>
        <span className="lab-session-user" title={usuario.identificador_acceso}>
          {usuario.identificador_acceso}
        </span>
      </div>
    </header>
  )
}
