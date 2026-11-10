import { useState } from 'react'
import { Link } from 'react-router-dom'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NuevaSolicitud from '../components/NuevaSolicitud.jsx'
import ResumenSolicitudes from '../components/ResumenSolicitudes.jsx'
import SolicitudesPanel from '../components/SolicitudesPanel.jsx'
import './laboratorio.css'

export default function LaboratorioPage({ usuario, logout }) {
  const [mostrarNuevaSolicitud, setMostrarNuevaSolicitud] = useState(false)
  const [solicitudCreada, setSolicitudCreada] = useState(null)
  const [vista, setVista] = useState('pendientes')
  const [indicador, setIndicador] = useState('todas')

  function seleccionarIndicador(codigo) {
    setIndicador(codigo)
    setVista('pendientes')
  }

  function cambiarVista(nueva) {
    setVista(nueva)
    if (nueva === 'finalizadas') setIndicador('todas')
  }

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
              <button className="primary-button" type="button" onClick={() => { setSolicitudCreada(null); setMostrarNuevaSolicitud(true) }}>+ Nueva solicitud</button>
            </div>
          </div>

          {solicitudCreada && <div className="lab-created-notice" role="status">
            <span>Solicitud <strong>{solicitudCreada.referencia}</strong> registrada para {solicitudCreada.paciente_nombre}.</span>
            <Link className="primary-button" to={`/laboratorio/solicitudes/${solicitudCreada.id}?accion=muestra`}>Registrar muestra ahora</Link>
            <button type="button" onClick={() => setSolicitudCreada(null)} aria-label="Cerrar aviso">×</button>
          </div>}

          <ResumenSolicitudes indicadorActivo={vista === 'pendientes' ? indicador : null} onSeleccionar={seleccionarIndicador} />
          <SolicitudesPanel vista={vista} onVistaChange={cambiarVista} indicador={indicador} onIndicadorChange={setIndicador} />
        </section>
      </div>
      {mostrarNuevaSolicitud && <NuevaSolicitud onClose={() => setMostrarNuevaSolicitud(false)} onCreated={setSolicitudCreada} />}
    </main>
  )
}
