import { useState } from 'react'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NuevaSolicitud from '../components/NuevaSolicitud.jsx'
import ResumenSolicitudes from '../components/ResumenSolicitudes.jsx'
import SolicitudesPanel from '../components/SolicitudesPanel.jsx'
import './laboratorio.css'

export default function LaboratorioPage({ usuario, logout }) {
  const [mostrarNuevaSolicitud, setMostrarNuevaSolicitud] = useState(false)
  const [solicitudCreada, setSolicitudCreada] = useState('')
  return (
    <main className="lab-page">
      <div className="lab-main">
        <LaboratorioTopbar usuario={usuario} onLogout={logout} />
        <section className="lab-content">
          <div className="lab-title-row">
            <div>
              <p className="lab-eyebrow">LABORATORIO</p>
              <h1>Solicitudes de laboratorio</h1>
            </div>
            <div className="lab-title-actions">
              <button className="primary-button" type="button" onClick={() => { setSolicitudCreada(''); setMostrarNuevaSolicitud(true) }}>+ Nueva solicitud</button>
            </div>
          </div>

          <ResumenSolicitudes />
          <SolicitudesPanel />

          {solicitudCreada && <p className="lab-created-notice" role="status">Solicitud {solicitudCreada} registrada.</p>}
        </section>
      </div>
      {mostrarNuevaSolicitud && <NuevaSolicitud onClose={() => setMostrarNuevaSolicitud(false)} onCreated={(solicitud) => setSolicitudCreada(solicitud.referencia)} />}
    </main>
  )
}
