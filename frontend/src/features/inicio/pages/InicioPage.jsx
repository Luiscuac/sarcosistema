import { Link, Navigate } from 'react-router-dom'
import { redireccionDesdeInicio } from '../../accesos/auth/destinos.js'
import './inicio.css'

export default function InicioPage({ usuario, logout }) {
  // Los roles con un solo módulo van directo a su pantalla: la bienvenida no les aporta nada.
  const destino = redireccionDesdeInicio(usuario.rol)
  if (destino) return <Navigate to={destino} replace />
  return (
    <main className="inicio-page">
      <header className="auth-topbar">SarcoSistema</header>
      <section className="inicio-content">
        <h1>Bienvenido a SarcoSistema</h1>
        <p>Sesión iniciada como <strong>{usuario.identificador_acceso}</strong>.</p>
        <p>Tu rol: <strong>{usuario.rol}</strong>.</p>
        {usuario.rol === 'medico' ? (
          <Link className="inicio-link" to="/consultas">Entrar a consulta médica</Link>
        ) : usuario.rol === 'laboratorio' ? (
          <Link className="inicio-link" to="/laboratorio">Entrar a laboratorio</Link>
        ) : usuario.rol === 'enfermeria' ? (
          <Link className="inicio-link" to="/enfermeria">Entrar a enfermeria</Link>
        ) : usuario.rol === 'imagenes' ? (
          <Link className="inicio-link" to="/imagenes">Entrar a radiología (ecografías)</Link>
        ) : (
          <p>El módulo para este rol todavía no está disponible en el piloto.</p>
        )}
        {usuario.rol === 'medico' && <>
          <Link className="inicio-link" to="/imagenes/rayos-x">Entrar a Rayos X</Link>
          <Link className="inicio-link" to="/ia">Transcripción experimental</Link>
        </>}
        <button className="primary-button" onClick={logout}>Cerrar sesión</button>
      </section>
    </main>
  )
}
