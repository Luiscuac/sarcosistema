import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import EstudioDetalle from '../components/EstudioDetalle.jsx'
import { listarEstudios } from '../api/imagenes.js'
import { mensajeError } from '../analisis.js'
import '../../laboratorio/pages/laboratorio.css'
import './rayos-x.css'

export default function RayosXPage({ usuario, logout }) {
  const [pagina, setPagina] = useState(1)
  const [seleccion, setSeleccion] = useState(null)
  const consulta = useQuery({ queryKey: ['imagenes', usuario.id, 'estudios', pagina], queryFn: ({ signal }) => listarEstudios(pagina, signal) })
  return <main className="lab-page rx-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo="Rayos X · Tórax" onLogout={logout} />
      <nav className="rx-nav" aria-label="Módulo de rayos X">
        <span aria-current="page">Estudios</span>
        <Link to="/consultas">Consulta médica</Link>
        <Link to="/inicio">Inicio</Link>
      </nav>
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
