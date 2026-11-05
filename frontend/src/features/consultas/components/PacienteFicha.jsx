import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useHistorial, usePaginaHistorial, usePaciente } from '../hooks/useConsultas.js'
import { obtenerSolicitudesLaboratorio } from '../api/consultasApi.js'
import { edad, fecha } from '../utils/paciente.js'
import SolicitarEcografia from './SolicitarEcografia.jsx'
import ExamenesComplementarios from './ExamenesComplementarios.jsx'

export function IdentidadPaciente({ paciente }) {
  return <div className="med-patient">
    <div><strong>{paciente.nombre_completo}</strong><span>HC {paciente.historia_clinica || 'No registrada'} · {paciente.codigo_paciente}</span></div>
    <dl>
      <div><dt>Documento</dt><dd>{paciente.numero_documento || 'Sin documento'}</dd></div>
      <div><dt>Nacimiento</dt><dd>{fecha(paciente.fecha_nacimiento)}</dd></div>
      <div><dt>Edad</dt><dd>{edad(paciente.fecha_nacimiento)}</dd></div>
      <div><dt>Sexo</dt><dd>{paciente.sexo || 'No registrado'}</dd></div>
    </dl>
  </div>
}

function estadoEstudio(estudio) {
  if (estudio.estado === 'publicado') return 'Publicado'
  if (estudio.estado === 'no_realizado') return 'No realizado'
  if (estudio.estado === 'pendiente_muestra') return 'Pendiente de muestra'
  return 'En preparación'
}

function SolicitudLaboratorioItem({ solicitud, pacienteId }) {
  const finalizada = solicitud.estudios.length > 0
    && solicitud.estudios.every((estudio) => ['publicado', 'no_realizado'].includes(estudio.estado))
  return <div className="med-lab-request">
    <div className="med-lab-request-row">
      <div className="med-lab-request-identity">
        <strong>{solicitud.referencia}</strong>
        <span>{fecha(solicitud.fecha_solicitud)} · {solicitud.estudios.length} {solicitud.estudios.length === 1 ? 'estudio' : 'estudios'}</span>
      </div>
      <span className={`med-lab-status ${finalizada ? 'med-lab-status-ready' : ''}`}>{finalizada ? 'Finalizada' : 'En proceso'}</span>
      {finalizada
        ? <Link className="med-lab-report-button" to={`/consultas/pacientes/${pacienteId}/laboratorio/${solicitud.id}/informe`}>Ver informe</Link>
        : <button className="med-lab-report-button" type="button" disabled title="Disponible cuando termine el laboratorio">Ver informe</button>}
    </div>
    <details className="med-lab-request-details">
      <summary>Ver estudios solicitados</summary>
      <ul>{solicitud.estudios.map((estudio) => <li key={estudio.estudio_id}>
        <div><strong>{estudio.tipo_estudio_nombre}</strong><span>{estadoEstudio(estudio)}</span></div>
        {estudio.incidencias.map((incidencia, index) => <p key={index}>Constancia: {incidencia.motivo === 'muestra_no_entregada' ? 'Muestra no entregada' : incidencia.motivo === 'toma_rechazada' ? 'Toma rechazada' : 'Toma no realizada'} · {incidencia.descripcion} · {incidencia.responsable} · {new Date(incidencia.fecha_hora).toLocaleString('es-BO')}</p>)}
      </li>)}</ul>
    </details>
  </div>
}

export default function PacienteFicha({ id, usuario }) {
  const pagina = usePaginaHistorial(id)
  const paciente = usePaciente(id)
  const historial = useHistorial(id, pagina.pagina)
  const laboratorio = useQuery({ queryKey: ['consultas', 'laboratorio', id], queryFn: () => obtenerSolicitudesLaboratorio(id) })
  if (paciente.isPending) return <p role="status">Cargando ficha del paciente…</p>
  if (paciente.isError) return <p role="alert">No se pudo cargar el paciente. Comprueba el acceso y vuelve a intentarlo.</p>
  return <>
    <div className="med-heading"><div><p className="med-eyebrow">FICHA CLÍNICA</p><h1>{paciente.data.nombre_completo}</h1></div><div className="med-heading-actions"><Link className="primary-button med-button-link" to={`/consultas/pacientes/${id}/nueva`}>+ Nueva consulta</Link><SolicitarEcografia pacienteId={id} usuario={usuario} /></div></div>
    <IdentidadPaciente paciente={paciente.data} />
    <section className="med-panel"><div className="med-panel-header"><h2>Solicitudes de laboratorio</h2></div>
      {laboratorio.isPending && <p className="med-message">Cargando solicitudes de laboratorio…</p>}
      {laboratorio.isError && <p role="alert" className="med-message">No se pudieron cargar las solicitudes de laboratorio.</p>}
      {laboratorio.data?.length === 0 && <p className="med-message">Este paciente no tiene solicitudes de laboratorio.</p>}
      {laboratorio.data?.map((solicitud) => <SolicitudLaboratorioItem key={solicitud.id} solicitud={solicitud} pacienteId={id} />)}
    </section>
    <ExamenesComplementarios estudios={historial.data?.estudios_imagen} />
    <section className="med-panel"><div className="med-panel-header"><h2>Historial de consultas</h2><span>Más recientes primero</span></div>
      {historial.isPending && <p role="status" className="med-message">Cargando historial…</p>}
      {historial.isError && <p role="alert" className="med-message">No se pudo recuperar el historial.</p>}
      {historial.data && (historial.data.items.length ? <div className="med-table-wrap"><table className="med-table"><thead><tr><th>Fecha</th><th>Médico</th><th>Motivo</th><th>Diagnóstico</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{historial.data.items.map(item => <tr key={item.id}><td>{fecha(item.fecha_hora_inicio)}</td><td>{item.medico_nombre}</td><td>{item.motivo_consulta}</td><td>{item.diagnostico_principal || 'No registrado'}</td><td><span className="med-badge">{item.estado}</span></td><td><Link to={`/consultas/${item.id}`}>Ver detalle</Link></td></tr>)}</tbody></table></div> : <p className="med-message">Este paciente no tiene consultas registradas.</p>)}
      {historial.data && <div className="med-pagination"><button disabled={pagina.pagina === 1} onClick={() => pagina.setPagina(x => x - 1)}>Anterior</button><span>Página {pagina.pagina} · {historial.data.total} consultas</span><button disabled={pagina.pagina * historial.data.limite >= historial.data.total} onClick={() => pagina.setPagina(x => x + 1)}>Siguiente</button></div>}
    </section>
  </>
}
