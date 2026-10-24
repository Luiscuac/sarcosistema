import { Link } from 'react-router-dom'
import TranscriptionForm from '../components/TranscriptionForm.jsx'
import './ia.css'

export default function IaPage({ usuario, logout }) {
  return (
    <main className="ia-page">
      <aside className="ia-sidebar">
        <div className="ia-sidebar-heading"><strong>SarcoSistema</strong><span>ASISTENCIA EXPERIMENTAL</span></div>
        <nav className="ia-nav" aria-label="Módulo de asistencia">
          <Link className="ia-nav-item ia-nav-item--inactive" to="/inicio">Inicio</Link>
          <span className="ia-nav-item ia-nav-item--active" aria-current="page">Transcripción</span>
        </nav>
        <button className="ia-signout" onClick={logout}>Cerrar sesión</button>
      </aside>

      <div className="ia-main">
        <header className="ia-topbar">
          <span>HERRAMIENTAS DE ASISTENCIA</span>
          <div className="ia-session">
            <span className="ia-session-status"><span aria-hidden="true" /> Sesión activa</span>
            <span className="ia-session-user" title={usuario.identificador_acceso}>{usuario.identificador_acceso}</span>
          </div>
        </header>

        <section className="ia-content">
          <div className="ia-title-row">
            <div><p className="ia-eyebrow">ASISTENCIA EXPERIMENTAL</p><h1>Transcripción de audio</h1>
              <p className="ia-intro">Convierte una grabación en texto para facilitar su revisión.</p></div>
            <span className="ia-view-label">Procesamiento local</span>
          </div>
          <div className="ia-notice" role="note">
            <span className="ia-notice-icon" aria-hidden="true">i</span>
            <p><strong>La transcripción no es un registro clínico.</strong> El texto generado es un borrador y debe ser revisado y confirmado por un profesional. No se guarda ni se publica automáticamente.</p>
          </div>
          <TranscriptionForm />
        </section>
      </div>
    </main>
  )
}
