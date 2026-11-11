import { Navigate } from 'react-router-dom'
import { redireccionDesdeInicio } from '../../accesos/auth/destinos.js'
import './inicio.css'

export default function InicioPage({ usuario, logout }) {
  // Cada rol entra directamente a su área de trabajo.
  const destino = redireccionDesdeInicio(usuario.rol)
  if (destino) return <Navigate to={destino} replace />
  return (
    <main className="inicio-page">
      <header className="auth-topbar">SarcoSistema</header>
      <section className="inicio-content">
        <h1>Bienvenido a SarcoSistema</h1>
        <p>Sesión iniciada como <strong>{usuario.identificador_acceso}</strong>.</p>
        <p>Tu rol: <strong>{usuario.rol}</strong>.</p>
        <p>El módulo para este rol todavía no está disponible en el piloto.</p>
        <button className="primary-button" onClick={logout}>Cerrar sesión</button>
      </section>
    </main>
  )
}
