import './IaTopbar.css'

export default function IaTopbar({ usuario }) {
  return (
    <header className="ia-topbar">
      <span>HERRAMIENTAS DE ASISTENCIA</span>
      <div className="ia-session">
        <span className="ia-session-status"><span aria-hidden="true" /> Sesión activa</span>
        <span className="ia-session-user" title={usuario.identificador_acceso}>
          {usuario.identificador_acceso}
        </span>
      </div>
    </header>
  )
}
