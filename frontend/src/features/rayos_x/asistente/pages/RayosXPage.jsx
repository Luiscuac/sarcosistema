import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ConsultasLayout from '../../../consultas/components/ConsultasLayout.jsx'
import EstudioDetalle from '../components/EstudioDetalle.jsx'
import DesempenoAsistente from '../components/DesempenoAsistente.jsx'
import { listarEstudios } from '../api/rayosXAiApi.js'
import { mensajeError } from '../analisis.js'
import '../../../laboratorio/pages/laboratorio.css'
import './rayos-x.css'

export default function RayosXPage({ usuario, logout }) {
  const [pagina, setPagina] = useState(1)
  const [parametros, setParametros] = useSearchParams()
  const [verDesempeno, setVerDesempeno] = useState(false)
  // Desde el informe del paciente se llega con ?estudio=ID: abrir directamente ese estudio.
  const [seleccion, setSeleccion] = useState(() => Number(parametros.get('estudio')) || null)
  const consulta = useQuery({ queryKey: ['imagenes', usuario.id, 'estudios', pagina], queryFn: ({ signal }) => listarEstudios(pagina, signal) })
  const volver = () => { setSeleccion(null); if (parametros.get('estudio')) setParametros({}, { replace: true }) }
  if (seleccion) return <ConsultasLayout usuario={usuario} logout={logout} area="rayos-x">
    <EstudioDetalle key={`${usuario.id}:${seleccion}`} id={seleccion} usuario={usuario} habilitada={consulta.data?.ia_habilitada} onVolver={volver} />
  </ConsultasLayout>
  return <ConsultasLayout usuario={usuario} logout={logout} area="rayos-x">
        <div className="lab-title-row"><div><p className="lab-eyebrow">RAYOS X</p><h1>Estudios radiológicos</h1><p className="lab-intro">Radiografías de tórax con informe publicado. Abre una para analizarla con el asistente.</p></div><button type="button" className="lab-secondary-button" aria-haspopup="dialog" onClick={() => setVerDesempeno(true)}>Desempeño del asistente</button></div>
        {verDesempeno && <DesempenoAsistente usuario={usuario} onCerrar={() => setVerDesempeno(false)} />}
        <p className="rx-advertencia">Prototipo universitario. La IA no diagnostica, no publica informes y no sustituye la revisión médica.</p>
        {consulta.isPending && <p role="status">Cargando estudios…</p>}
        {consulta.error && <p role="alert">{mensajeError(consulta.error)}</p>}
        {consulta.data && <>
          {!consulta.data.estudios.length && <p>No hay estudios publicados disponibles para tu cuenta.</p>}
          <div className="rx-tabla lab-list-panel lab-table-wrap"><table className="lab-table"><thead><tr><th>Referencia</th><th>Paciente</th><th>Estudio</th><th>Acción</th></tr></thead><tbody>
            {consulta.data.estudios.map(e => <tr key={e.id}><td>{e.referencia}</td><td>{e.paciente}<br /><small>{e.codigo_paciente}</small></td><td>{e.estudio}</td><td><button type="button" className="lab-secondary-button" onClick={() => { setSeleccion(e.id); window.scrollTo(0, 0) }}>Abrir</button></td></tr>)}
          </tbody></table></div>
          <div className="lab-actions"><button type="button" className="lab-secondary-button" disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>Anterior</button><span>Página {pagina}</span><button type="button" className="lab-secondary-button" disabled={consulta.data.estudios.length < 20} onClick={() => setPagina(p => p + 1)}>Siguiente</button></div>
        </>}
  </ConsultasLayout>
}
