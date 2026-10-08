import { useAuth } from '../../context/AuthContext'
import FormularioExamen from '../../components/laboratorio/FormularioExamen'
import '../../assets/styles/laboratorio.css'

export default function LaboratorioPage() {
  const { usuario, logout } = useAuth()

  return (
    <div className="lab-container">
      <header className="lab-header">
        <h1>Módulo de Laboratorio</h1>
        <div className="user-info">
          <span>Hola, {usuario?.nombre_usuario} ({usuario?.rol})</span>
          <button onClick={logout} className="logout-btn">Cerrar Sesión</button>
        </div>
      </header>
      
      <main className="lab-content">
        <section className="lab-section">
          <h2>Registrar nuevo examen (HU-N05)</h2>
          {/* Para probar enviamos un ID estático 1 (asumiendo que existe paciente 1 en la BD) */}
          <FormularioExamen pacienteId={1} onCreado={(ex) => alert(`Examen creado ID: ${ex.id}`)} />
        </section>
      </main>
    </div>
  )
}
