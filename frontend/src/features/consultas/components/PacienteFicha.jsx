import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useHistorial, usePaciente } from '../hooks/useConsultas.js'

export function fecha(valor) { return valor ? new Date(`${valor.slice(0, 10)}T12:00:00`).toLocaleDateString('es-BO') : 'No registrada' }
export function edad(nacimiento) {
  if (!nacimiento) return 'No registrada'
  const hoy = new Date()
  const nacio = new Date(`${nacimiento.slice(0, 10)}T12:00:00`)
  return `${hoy.getFullYear() - nacio.getFullYear() - (hoy.getMonth() < nacio.getMonth() || (hoy.getMonth() === nacio.getMonth() && hoy.getDate() < nacio.getDate()) ? 1 : 0)} años`
}

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

export default function PacienteFicha({ id }) {
  const pagina = useHistorialPage(id)
  const paciente = usePaciente(id)
  const historial = useHistorial(id, pagina.pagina)
  if (paciente.isPending) return <p role="status">Cargando ficha del paciente…</p>
  if (paciente.isError) return <p role="alert">No se pudo cargar el paciente. Comprueba el acceso y vuelve a intentarlo.</p>
  return <>
    <div className="med-heading"><div><p className="med-eyebrow">FICHA CLÍNICA</p><h1>{paciente.data.nombre_completo}</h1></div><Link className="primary-button med-button-link" to={`/consultas/pacientes/${id}/nueva`}>+ Nueva consulta</Link></div>
    <IdentidadPaciente paciente={paciente.data} />
    <section className="med-panel"><div className="med-panel-header"><h2>Historial de consultas</h2><span>Más recientes primero</span></div>
      {historial.isPending && <p role="status" className="med-message">Cargando historial…</p>}
      {historial.isError && <p role="alert" className="med-message">No se pudo recuperar el historial.</p>}
      {historial.data && (historial.data.items.length ? <div className="med-table-wrap"><table className="med-table"><thead><tr><th>Fecha</th><th>Médico</th><th>Motivo</th><th>Diagnóstico</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{historial.data.items.map(item => <tr key={item.id}><td>{fecha(item.fecha_hora_inicio)}</td><td>{item.medico_nombre}</td><td>{item.motivo_consulta}</td><td>{item.diagnostico_principal || 'No registrado'}</td><td><span className="med-badge">{item.estado}</span></td><td><Link to={`/consultas/${item.id}`}>Ver detalle</Link></td></tr>)}</tbody></table></div> : <p className="med-message">Este paciente no tiene consultas registradas.</p>)}
      {historial.data && <div className="med-pagination"><button disabled={pagina.pagina === 1} onClick={() => pagina.setPagina(x => x - 1)}>Anterior</button><span>Página {pagina.pagina} · {historial.data.total} consultas</span><button disabled={pagina.pagina * historial.data.limite >= historial.data.total} onClick={() => pagina.setPagina(x => x + 1)}>Siguiente</button></div>}
    </section>
  </>
}

function useHistorialPage(id) {
  const [pagina, setPagina] = useState(1)
  useEffect(() => { setPagina(1) }, [id])
  return { pagina, setPagina }
}
