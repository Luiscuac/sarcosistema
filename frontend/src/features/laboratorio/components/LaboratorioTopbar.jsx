import { Link } from 'react-router-dom'

/** Barra superior compartida. `inicio` es la pantalla principal del servicio que muestra la barra. */
export default function LaboratorioTopbar({ usuario, onLogout, titulo = 'Laboratorio', inicio = '/laboratorio' }) {
  return (
    <header className="lab-topbar">
      <Link className="lab-brand" to={inicio} title={`Ir al inicio de ${titulo}`}>
        <strong>SarcoSistema</strong>
        <span>{titulo}</span>
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
