import { Link } from 'react-router-dom'
import './inicio.css'

export default function InicioPage({ usuario, logout }) {
  return (
    <main className="inicio-page">
      <header className="auth-topbar">SarcoSistema</header>
      <section className="inicio-content">
        <h1>Bienvenido a SarcoSistema</h1>
        <p>Sesión iniciada como <strong>{usuario.identificador_acceso}</strong>.</p>
        <p>Tu rol: <strong>{usuario.rol}</strong>.</p>
        {usuario.rol === 'laboratorio' ? (
          <Link className="inicio-link" to="/laboratorio">Entrar a laboratorio</Link>
        ) : (
          <p>El módulo para este rol todavía no está disponible en el piloto.</p>
        )}
        <button className="primary-button" onClick={logout}>Cerrar sesión</button>
      </section>
    </main>
  )
}
