import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { usePacientes } from '../hooks/useConsultas.js'
import { edad } from '../components/PacienteFicha.jsx'
import PacienteFicha from '../components/PacienteFicha.jsx'
import ConsultaFormulario from '../components/ConsultaFormulario.jsx'
import ConsultaDetalle from '../components/ConsultaDetalle.jsx'
import './consultas.css'

function Busqueda() {
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)
  useEffect(() => {
    const timer = setTimeout(() => { setBuscar(entrada.trim()); setPagina(1) }, 350)
    return () => clearTimeout(timer)
  }, [entrada])
  const consulta = usePacientes(buscar, pagina)
  return <><div className="med-heading"><div><p className="med-eyebrow">CONSULTA MÉDICA</p><h1>Buscar paciente</h1><p>Identifica a la persona por nombre, documento, historia clínica o código antes de abrir su ficha.</p></div></div>
    <section className="med-panel"><div className="med-panel-header"><h2>Pacientes registrados</h2><span>Busca al menos dos caracteres</span></div><label className="med-search">Buscar paciente<input autoFocus type="search" value={entrada} onChange={e => setEntrada(e.target.value)} placeholder="Nombre, CI, historia clínica o código" /></label>
      {buscar.length < 2 ? <p className="med-message">Escribe al menos dos caracteres para comenzar.</p> : consulta.isPending ? <p role="status" className="med-message">Buscando pacientes…</p> : consulta.isError ? <p role="alert" className="med-message">No se pudo buscar. Comprueba la conexión e inténtalo de nuevo.</p> : !consulta.data.items.length ? <p className="med-message">No se encontraron pacientes con ese criterio.</p> : <div className="med-table-wrap"><table className="med-table"><thead><tr><th>Paciente</th><th>Historia clínica / Código</th><th>Documento</th><th>Edad</th><th>Sexo</th><th>Acción</th></tr></thead><tbody>{consulta.data.items.map(p => <tr key={p.id}><td><strong>{p.nombre_completo}</strong></td><td>{p.historia_clinica || 'No registrada'}<small>{p.codigo_paciente}</small></td><td>{p.numero_documento || 'Sin documento'}</td><td>{edad(p.fecha_nacimiento)}</td><td>{p.sexo}</td><td><Link to={`/consultas/pacientes/${p.id}`}>Abrir ficha</Link></td></tr>)}</tbody></table></div>}
      {consulta.data && <div className="med-pagination"><button disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>Anterior</button><span>Página {pagina} · {consulta.data.total} resultados</span><button disabled={pagina * consulta.data.limite >= consulta.data.total} onClick={() => setPagina(p => p + 1)}>Siguiente</button></div>}
    </section>
  </>
}

export default function ConsultasPage({ usuario, logout, vista = 'busqueda' }) {
  const { pacienteId, consultaId } = useParams()
  return <main className="med-page"><aside className="med-sidebar"><div className="med-sidebar-heading"><strong>SarcoSistema</strong><span>CONSULTA MÉDICA</span></div><nav aria-label="Módulo médico"><Link className="med-nav-active" to="/consultas">Pacientes y consultas</Link><Link to="/inicio">Inicio</Link></nav><button className="med-signout" onClick={logout}>Cerrar sesión</button></aside><div className="med-main"><header className="med-topbar"><span>CONSULTA EXTERNA</span><div><span className="med-session">● Sesión activa</span><strong>{usuario.identificador_acceso}</strong></div></header><section className="med-content">{vista === 'ficha' ? <PacienteFicha id={pacienteId} /> : vista === 'nueva' ? <ConsultaFormulario id={pacienteId} usuario={usuario} /> : vista === 'detalle' ? <ConsultaDetalle id={consultaId} /> : <Busqueda />}</section></div></main>
}
