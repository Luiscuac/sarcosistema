import LaboratorioSidebar from '../components/LaboratorioSidebar.jsx'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import ResumenSolicitudes from '../components/ResumenSolicitudes.jsx'
import SolicitudesPanel from '../components/SolicitudesPanel.jsx'
import './laboratorio.css'

export default function LaboratorioPage({ usuario, logout }) {
  return (
    <main className="lab-page">
      <LaboratorioSidebar onLogout={logout} />
      <div className="lab-main">
        <LaboratorioTopbar usuario={usuario} />
        <section className="lab-content">
          <div className="lab-title-row">
            <div>
              <p className="lab-eyebrow">LABORATORIO</p>
              <h1>Solicitudes de laboratorio</h1>
              <p className="lab-intro">Seguimiento de estudios y resultados asociados a cada paciente.</p>
            </div>
            <span className="lab-view-label">Vista inicial</span>
          </div>

          <ResumenSolicitudes />
          <SolicitudesPanel />

          <div className="lab-actions">
            <button className="primary-button" type="button" disabled>Nueva solicitud</button>
            <span>Las acciones de laboratorio estarán disponibles cuando se conecte este flujo.</span>
          </div>
        </section>
      </div>
    </main>
  )
}
