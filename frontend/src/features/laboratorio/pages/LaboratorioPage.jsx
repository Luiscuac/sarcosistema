import { useState } from 'react'
import LaboratorioSidebar from '../components/LaboratorioSidebar.jsx'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NuevaSolicitud from '../components/NuevaSolicitud.jsx'
import ResumenSolicitudes from '../components/ResumenSolicitudes.jsx'
import SolicitudesPanel from '../components/SolicitudesPanel.jsx'
import RecibirMuestra from '../components/RecibirMuestra.jsx'
import ResultadoEstudio from '../components/ResultadoEstudio.jsx'
import './laboratorio.css'

export default function LaboratorioPage({ usuario, logout }) {
  const [mostrarNuevaSolicitud, setMostrarNuevaSolicitud] = useState(false)
  const [solicitudCreada, setSolicitudCreada] = useState('')
  const [solicitudMuestra, setSolicitudMuestra] = useState(null)
  const [estudioResultado, setEstudioResultado] = useState(null)
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
          <SolicitudesPanel onRecibirMuestra={setSolicitudMuestra} onAbrirResultado={setEstudioResultado} />

          <div className="lab-actions">
            <button className="primary-button" type="button" onClick={() => { setSolicitudCreada(''); setMostrarNuevaSolicitud(true) }}>Nueva solicitud</button>
            {solicitudCreada && <span role="status">Solicitud {solicitudCreada} registrada.</span>}
          </div>
        </section>
      </div>
      {mostrarNuevaSolicitud && <NuevaSolicitud onClose={() => setMostrarNuevaSolicitud(false)} onCreated={(solicitud) => setSolicitudCreada(solicitud.referencia)} />}
      {solicitudMuestra && <RecibirMuestra solicitud={solicitudMuestra} onClose={() => setSolicitudMuestra(null)} onReceived={() => setSolicitudMuestra(null)} />}
      {estudioResultado && <ResultadoEstudio estudio={estudioResultado} onClose={() => setEstudioResultado(null)} />}
    </main>
  )
}
