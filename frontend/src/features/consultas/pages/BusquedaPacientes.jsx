import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePacientes } from '../hooks/useConsultas.js'
import { edad } from '../utils/paciente.js'
import { nombreSexo } from '../../../shared/utils/personas.js'

export default function BusquedaPacientes() {
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)

  useEffect(() => {
    const timer = setTimeout(() => { setBuscar(entrada.trim()); setPagina(1) }, 350)
    return () => clearTimeout(timer)
  }, [entrada])

  const consulta = usePacientes(buscar, pagina)
  const termino = entrada.trim()
  const esperandoBusqueda = termino !== buscar

  return <>
    <div className="med-heading med-search-heading">
      <div>
        <p className="med-eyebrow">CONSULTA MÉDICA</p>
        <h1>Buscar pacientes</h1>
        <p>Encuentra una ficha por nombre, documento o historia clínica.</p>
      </div>
    </div>
    <section className="med-search-workspace" aria-label="Búsqueda de pacientes">
      <label className="med-search-field">
        <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
        <span className="sr-only">Buscar por nombre, documento, historia clínica o código</span>
        <input
          type="search"
          value={entrada}
          onChange={e => setEntrada(e.target.value)}
          placeholder="Nombre, CI, historia clínica o código"
          aria-describedby="med-search-hint"
        />
        {entrada && <button type="button" onClick={() => setEntrada('')} aria-label="Limpiar búsqueda">Limpiar</button>}
      </label>
      <p className="med-search-hint" id="med-search-hint">Escribe al menos dos caracteres para buscar.</p>

      {termino.length < 2
        ? <div className="med-search-state">
          <span className="med-search-state-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
          </span>
          <div><h2>Busca una ficha de paciente</h2><p>Los resultados aparecerán aquí mientras escribes.</p></div>
        </div>
        : esperandoBusqueda || consulta.isPending
          ? <div className="med-search-state" role="status">
            <span className="med-search-spinner" aria-hidden="true" />
            <div><h2>Buscando pacientes</h2><p>Estamos consultando las fichas que coinciden.</p></div>
          </div>
          : consulta.isError
            ? <div className="med-search-state med-search-state--error" role="alert">
              <div><h2>No se pudo completar la búsqueda</h2><p>Comprueba la conexión e inténtalo de nuevo.</p></div>
              <button type="button" className="med-search-retry" onClick={() => consulta.refetch()}>Reintentar</button>
            </div>
            : !consulta.data.items.length
              ? <div className="med-search-state">
                <div><h2>No encontramos coincidencias</h2><p>Prueba con otro nombre, documento o código.</p></div>
              </div>
              : <>
                <div className="med-search-results-heading">
                  <div><h2>Resultados <span>{consulta.data.total}</span></h2><p>Coincidencias para <strong>“{buscar}”</strong></p></div>
                </div>
                <ul className="med-patient-results" aria-label="Pacientes encontrados">
                  {consulta.data.items.map(p => {
                    const iniciales = p.nombre_completo.trim().split(/\s+/).slice(0, 2).map(parte => parte[0]).join('').toUpperCase()
                    return <li className="med-patient-result" key={p.id}>
                      <div className="med-result-person">
                        <span className="med-result-avatar" aria-hidden="true">{iniciales}</span>
                        <div><h3>{p.nombre_completo}</h3><p>{p.numero_documento || 'Sin documento registrado'}</p></div>
                      </div>
                      <dl className="med-result-data">
                        <div><dt>Historia clínica</dt><dd>{p.historia_clinica || 'No registrada'}</dd></div>
                        <div><dt>Código</dt><dd>{p.codigo_paciente}</dd></div>
                        <div><dt>Edad · sexo</dt><dd>{edad(p.fecha_nacimiento)} · {p.sexo ? nombreSexo(p.sexo) : 'No registrado'}</dd></div>
                      </dl>
                      <Link className="med-result-action" to={`/consultas/pacientes/${p.id}`}>Abrir ficha <span aria-hidden="true">→</span></Link>
                    </li>
                  })}
                </ul>
                <div className="med-search-pagination">
                  <span>Página {pagina} de {Math.max(1, Math.ceil(consulta.data.total / consulta.data.limite))}</span>
                  <div>
                    <button disabled={pagina === 1} onClick={() => setPagina(p => p - 1)}>Anterior</button>
                    <button disabled={pagina * consulta.data.limite >= consulta.data.total} onClick={() => setPagina(p => p + 1)}>Siguiente</button>
                  </div>
                </div>
              </>}
    </section>
  </>
}
