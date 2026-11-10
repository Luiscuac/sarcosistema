import { useParams } from 'react-router-dom'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NavegacionLab from '../components/NavegacionLab.jsx'
import ResultadoEstudio from '../components/ResultadoEstudio.jsx'
import './laboratorio.css'
import './resultado-estudio.css'

export default function ResultadoEstudioPage({ usuario, logout }) {
  const { solicitudId, estudioId } = useParams()
  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-result-page">
        <NavegacionLab volverA={`/laboratorio/solicitudes/${solicitudId}`} textoVolver="Volver a la solicitud" migas={[
          { texto: 'Solicitudes', ruta: '/laboratorio' },
          { texto: 'Solicitud', ruta: `/laboratorio/solicitudes/${solicitudId}` },
          { texto: 'Resultado' },
        ]} />
        <ResultadoEstudio estudioId={estudioId} usuario={usuario} />
      </section>
    </div>
  </main>
}
