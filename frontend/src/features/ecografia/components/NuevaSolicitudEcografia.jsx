import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Dialogo from '../../../shared/ui/Dialogo.jsx'
import { buscarPacientes, crearSolicitud, obtenerCatalogo } from '../api/ecografiaApi.js'

export default function NuevaSolicitudEcografia({ onCerrar, onCreada }) {
  const cache = useQueryClient()
  const clave = useRef(crypto.randomUUID())
  const [entrada, setEntrada] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [paciente, setPaciente] = useState(null)
  const [tipos, setTipos] = useState([])
  const [medico, setMedico] = useState('')
  const [urgente, setUrgente] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const pacientes = useQuery({ queryKey: ['ecografia', 'pacientes', busqueda], queryFn: () => buscarPacientes(busqueda), enabled: busqueda.length >= 2 })
  const catalogo = useQuery({ queryKey: ['ecografia', 'catalogo'], queryFn: obtenerCatalogo })

  async function enviar(e) {
    e.preventDefault(); setError(''); setOcupado(true)
    try {
      const resultado = await crearSolicitud({ paciente_id: paciente.id, tipo_estudio_ids: tipos, medico_solicitante_nombre: medico.trim(), prioridad: urgente ? 'urgente' : 'sin_prioridad', clave_idempotencia: clave.current })
      await cache.invalidateQueries({ queryKey: ['ecografia', 'bandeja'] })
      onCreada?.({ ...resultado, paciente: paciente.nombre_completo, cantidad: tipos.length })
      onCerrar()
    } catch (err) { setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo crear la solicitud.') }
    finally { setOcupado(false) }
  }

  return <Dialogo titulo="Nueva solicitud de ecografía" eyebrow="ECOGRAFÍA" onCerrar={onCerrar} bloqueado={ocupado}>
    <div className="lab-dialog-body eco-solicitud">
      <div className="eco-modal-intro"><span className="eco-section-number">1</span><div><h3>Identifica al paciente</h3><p>Busca y selecciona a la persona que recibirá el estudio.</p></div></div>
      <form className="eco-patient-search" onSubmit={e => { e.preventDefault(); setBusqueda(entrada.trim()); setPaciente(null) }}><label>Nombre, documento o código<input minLength={2} maxLength={100} value={entrada} onChange={e => setEntrada(e.target.value)} placeholder="Escribe al menos dos caracteres" required /></label><button className="lab-secondary-button" type="submit" disabled={ocupado}>Buscar paciente</button></form>
      {pacientes.isFetching && <p role="status">Buscando pacientes…</p>}
      {pacientes.isError && <p role="alert">No se pudo buscar al paciente.</p>}
      {pacientes.data?.items.length === 0 && <p>No se encontraron pacientes.</p>}
      <div className="eco-resultados">{pacientes.data?.items.map(p => <button key={p.id} className={`lab-secondary-button${paciente?.id === p.id ? ' eco-seleccionado' : ''}`} type="button" disabled={ocupado} onClick={() => setPaciente(p)} aria-pressed={paciente?.id === p.id}>{p.nombre_completo} · {p.codigo_paciente}</button>)}</div>
      <form id="eco-nueva-solicitud" onSubmit={enviar}><fieldset disabled={ocupado}><legend>Solicitud</legend>
        {paciente ? <div className="eco-patient-selected"><span>Paciente seleccionado</span><strong>{paciente.nombre_completo}</strong><small>{paciente.codigo_paciente}</small></div> : <p className="eco-ayuda">Selecciona al paciente antes de crear la solicitud.</p>}
        <div className="eco-modal-intro"><span className="eco-section-number">2</span><div><h3>Indica los estudios</h3><p>Puedes incluir varias ecografías en la misma solicitud.</p></div></div>
        <label>Médico solicitante<input required minLength={2} maxLength={200} value={medico} onChange={e => setMedico(e.target.value)} /></label>
        {catalogo.isPending && <p role="status">Cargando estudios…</p>}{catalogo.isError && <p role="alert">No se pudo cargar el catálogo.</p>}
        <div className="eco-tipos">{catalogo.data?.map(t => <label className={tipos.includes(t.id) ? 'is-selected' : ''} key={t.id}><input type="checkbox" checked={tipos.includes(t.id)} onChange={() => setTipos(actual => actual.includes(t.id) ? actual.filter(i => i !== t.id) : [...actual, t.id])} />{t.nombre}</label>)}</div>
        <label className="eco-check"><input type="checkbox" checked={urgente} onChange={e => setUrgente(e.target.checked)} />Prioridad urgente</label>
      </fieldset></form>
      {error && <p role="alert">{error}</p>}
    </div><footer className="lab-dialog-footer"><p className="lab-dialog-summary">{tipos.length} {tipos.length === 1 ? 'estudio seleccionado' : 'estudios seleccionados'}</p><button type="button" disabled={ocupado} onClick={onCerrar}>Cancelar</button><button form="eco-nueva-solicitud" type="submit" className="primary-button" disabled={ocupado || !paciente || !tipos.length || medico.trim().length < 2}>{ocupado ? 'Creando…' : 'Crear solicitud'}</button></footer>
  </Dialogo>
}
