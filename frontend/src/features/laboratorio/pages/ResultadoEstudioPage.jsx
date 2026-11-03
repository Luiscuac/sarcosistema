import { Link, useParams } from 'react-router-dom'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import ResultadoEstudio from '../components/ResultadoEstudio.jsx'
import './laboratorio.css'
import './resultado-estudio.css'

export default function ResultadoEstudioPage({ usuario, logout }) {
  const { solicitudId, estudioId } = useParams()
  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-result-page">
        <Link className="lab-back-link" to={`/laboratorio/solicitudes/${solicitudId}`}>← Volver a la solicitud</Link>
        <ResultadoEstudio estudioId={estudioId} />
      </section>
    </div>
  </main>
}
