import { Link } from 'react-router-dom'
import './marco.css'

/** Barra superior de los servicios (Laboratorio, Ecografía, Rayos X…): `titulo` y `inicio` los da cada módulo. */
export default function BarraSuperior({ usuario, onLogout, titulo, inicio }) {
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
