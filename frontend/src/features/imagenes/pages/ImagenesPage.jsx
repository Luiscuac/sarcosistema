import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import LaboratorioSidebar from '../../laboratorio/components/LaboratorioSidebar.jsx'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import EstudioDetalle from '../components/EstudioDetalle.jsx'
import { listarEstudios } from '../api/imagenes.js'
import { mensajeError } from '../analisis.js'
import '../../laboratorio/pages/laboratorio.css'
import './imagenes.css'

export default function ImagenesPage({ usuario, logout }) {
  const [pagina, setPagina] = useState(1)
  const [seleccion, setSeleccion] = useState(null)
  const consulta = useQuery({ queryKey: ['imagenes', usuario.id, 'estudios', pagina], queryFn: ({ signal }) => listarEstudios(pagina, signal) })
  return <main className="lab-page">
    <LaboratorioSidebar onLogout={logout} titulo="RAYOS X" navegacion={<>
      <span className="lab-nav-item lab-nav-item--active" aria-current="page">Estudios</span>
      <Link className="lab-nav-item" to="/consultas">Consulta médica</Link>
      <Link className="lab-nav-item" to="/inicio">Inicio</Link>
    </>} />
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo="IMAGENOLOGÍA · TÓRAX" />
      <section className="lab-content">
        <div className="lab-title-row"><div><p className="lab-eyebrow">RAYOS X</p><h1>Estudios radiológicos</h1><p className="lab-intro">Informes publicados de tus solicitudes y asistencia experimental local.</p></div></div>
        <p className="rx-advertencia">Prototipo universitario. La IA no diagnostica, no publica informes y no sustituye la revisión médica.</p>
        {consulta.isPending && <p role="status">Cargando estudios…</p>}
        {consulta.error && <p role="alert">{mensajeError(consulta.error)}</p>}
        {consulta.data && <>
          {!consulta.data.estudios.length && <p>No hay estudios publicados disponibles para tu cuenta.</p>}
          <div className="rx-tabla"><table><thead><tr><th>Referencia</th><th>Paciente</th><th>Estudio</th><th>Acción</th></tr></thead><tbody>
            {consulta.data.estudios.map(e => <tr key={e.id}><td>{e.referencia}</td><td>{e.paciente}<br /><small>{e.codigo_paciente}</small></td><td>{e.estudio}</td><td><button type="button" className="secondary-button" onClick={() => setSeleccion(e.id)}>Ver estudio</button></td></tr>)}
          </tbody></table></div>
          <div className="lab-actions"><button type="button" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>Anterior</button><span>Página {pagina}</span><button type="button" disabled={consulta.data.estudios.length < 20} onClick={() => setPagina(p => p + 1)}>Siguiente</button></div>
        </>}
        {seleccion && <EstudioDetalle key={`${usuario.id}:${seleccion}`} id={seleccion} usuario={usuario} habilitada={consulta.data?.ia_habilitada} />}
      </section>
    </div>
  </main>
}
