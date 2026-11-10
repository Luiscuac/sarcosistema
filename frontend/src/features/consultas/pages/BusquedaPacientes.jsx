import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePacientes } from '../hooks/useConsultas.js'
import { edad } from '../utils/paciente.js'

export default function BusquedaPacientes() {
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => { setBuscar(entrada.trim()); setPagina(1) }, 350)
    return () => clearTimeout(timer)
  }, [entrada])

  const consulta = usePacientes(buscar, pagina)

  return <>
    <div className="med-heading"><div><p className="med-eyebrow">CONSULTA MÉDICA</p><h1>Buscar paciente</h1><p>Identifica a la persona por nombre, documento, historia clínica o código antes de abrir su ficha.</p></div></div>
    <section className="med-panel"><div className="med-panel-header"><h2>Pacientes registrados</h2><span>Busca al menos dos caracteres</span></div><label className="med-search">Buscar paciente<input autoFocus type="search" value={entrada} onChange={e => setEntrada(e.target.value)} placeholder="Nombre, CI, historia clínica o código" /></label>
      {buscar.length < 2 ? <p className="med-message">Escribe al menos dos caracteres para comenzar.</p> : consulta.isPending ? <p role="status" className="med-message">Buscando pacientes…</p> : consulta.isError ? <p role="alert" className="med-message">No se pudo buscar. Comprueba la conexión e inténtalo de nuevo.</p> : !consulta.data.items.length ? <p className="med-message">No se encontraron pacientes con ese criterio.</p> : <div className="med-table-wrap"><table className="med-table"><thead><tr><th>Paciente</th><th>Historia clínica / Código</th><th>Documento</th><th>Edad</th><th>Sexo</th><th>Acción</th></tr></thead><tbody>{consulta.data.items.map(p => <tr key={p.id}><td><strong>{p.nombre_completo}</strong></td><td>{p.historia_clinica || 'No registrada'}<small>{p.codigo_paciente}</small></td><td>{p.numero_documento || 'Sin documento'}</td><td>{edad(p.fecha_nacimiento)}</td><td>{p.sexo}</td><td><Link to={`/consultas/pacientes/${p.id}`}>Abrir ficha</Link></td></tr>)}</tbody></table></div>}
      {consulta.data && <div className="med-pagination"><button disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>Anterior</button><span>Página {pagina} · {consulta.data.total} resultados</span><button disabled={pagina * consulta.data.limite >= consulta.data.total} onClick={() => setPagina(p => p + 1)}>Siguiente</button></div>}
    </section>
  </>
}
