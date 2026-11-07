import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  actualizarBorradorEnfermeria, buscarPacientesEnfermeria,
  guardarBorradorEnfermeria, obtenerRegistrosEnfermeria,
  publicarRegistroEnfermeria,
} from '../api/enfermeriaApi.js'
import './enfermeria.css'

const inicial = {
  motivo_consulta: '', sintomas: '', observaciones_enfermeria: '',
  peso_kg: '', talla_cm: '', temperatura_c: '', frecuencia_cardiaca: '',
  frecuencia_respiratoria: '', presion_sistolica: '', presion_diastolica: '',
  saturacion_oxigeno: '', dolor_escala: '',
}
const narrativas = [
  ['motivo_consulta', 'Motivo referido por el paciente'],
  ['sintomas', 'Síntomas referidos'],
  ['observaciones_enfermeria', 'Observaciones de enfermería'],
]
const mediciones = [
  ['peso_kg', 'Peso (kg)'], ['talla_cm', 'Talla (cm)'],
  ['temperatura_c', 'Temperatura (°C)'], ['frecuencia_cardiaca', 'Frecuencia cardíaca (lat/min)'],
  ['frecuencia_respiratoria', 'Frecuencia respiratoria (resp/min)'],
  ['presion_sistolica', 'Presión sistólica (mmHg)'], ['presion_diastolica', 'Presión diastólica (mmHg)'],
  ['saturacion_oxigeno', 'Saturación de oxígeno (%)'], ['dolor_escala', 'Dolor (0 a 10)'],
]
const valores = (registro) => Object.fromEntries(Object.keys(inicial).map((campo) => [
  campo, registro?.[campo] == null ? '' : String(registro[campo]),
]))
const fechaHora = (value) => value ? new Date(value).toLocaleString('es-BO') : 'Sin fecha'
function edadPaciente(nacimiento) {
  if (!nacimiento) return 'Edad no registrada'
  const hoy = new Date()
  const fecha = new Date(`${nacimiento.slice(0, 10)}T12:00:00`)
  const cumpleEsteAnio = hoy.getMonth() > fecha.getMonth()
    || (hoy.getMonth() === fecha.getMonth() && hoy.getDate() >= fecha.getDate())
  return `${hoy.getFullYear() - fecha.getFullYear() - (cumpleEsteAnio ? 0 : 1)} años`
}

function CampoTexto({ campo, etiqueta, form, onChange }) {
  return <label className="enf-field">{etiqueta}<textarea rows={3} value={form[campo]} onChange={onChange} /></label>
}

function RegistroResumen({ registro, onEditar, onPublicar, ocupado }) {
  const items = [...narrativas, ...mediciones].filter(([campo]) => registro[campo] != null && registro[campo] !== '')
  return <article className="enf-record">
    <header><div><strong>{registro.estado === 'publicado' ? 'Publicado' : 'Borrador'}</strong>
      <span>{fechaHora(registro.publicado_en || registro.creado_en)}</span></div>
      {registro.estado === 'publicado' && <span className="enf-published">Visible para el médico</span>}</header>
    <dl>{items.map(([campo, etiqueta]) => <div key={campo}><dt>{etiqueta}</dt><dd>{registro[campo]}</dd></div>)}</dl>
    {registro.estado === 'borrador' && <div className="enf-actions">
      <button type="button" onClick={() => onEditar(registro)} disabled={ocupado}>Editar borrador</button>
      <button type="button" className="primary-button" onClick={() => onPublicar(registro.id)} disabled={ocupado}>Publicar para el médico</button>
    </div>}
  </article>
}

export default function EnfermeriaPage({ usuario, logout }) {
  const cache = useQueryClient()
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)
  const [paciente, setPaciente] = useState(null)
  const [form, setForm] = useState(inicial)
  const [edicion, setEdicion] = useState(null)
  const [ocupado, setOcupado] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const timer = setTimeout(() => { setBuscar(entrada.trim()); setPagina(1) }, 350)
    return () => clearTimeout(timer)
  }, [entrada])

  const pacientes = useQuery({
    queryKey: ['enfermeria', 'pacientes', buscar, pagina],
    queryFn: () => buscarPacientesEnfermeria(buscar, pagina),
    enabled: buscar.length >= 2,
  })
  const registros = useQuery({
    queryKey: ['enfermeria', 'registros', paciente?.id],
    queryFn: () => obtenerRegistrosEnfermeria(paciente.id),
    enabled: Boolean(paciente?.id),
  })

  function elegirPaciente(item) {
    if (Object.values(form).some(Boolean)
        && !window.confirm('Hay datos sin guardar. ¿Quieres cambiar de paciente y descartarlos?')) return
    setPaciente(item)
    setForm(inicial)
    setEdicion(null)
    setMensaje('')
    setError('')
  }

  async function guardar(evento) {
    evento.preventDefault()
    if (ocupado || !paciente) return
    setOcupado(true); setError(''); setMensaje('')
    const datos = Object.fromEntries(Object.entries(form).map(([campo, valor]) => [
      campo, valor.trim() === '' ? null : (campo === 'motivo_consulta' || campo === 'sintomas' || campo === 'observaciones_enfermeria' ? valor.trim() : Number(valor)),
    ]))
    try {
      if (edicion) await actualizarBorradorEnfermeria(edicion, datos)
      else await guardarBorradorEnfermeria(paciente.id, datos)
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', paciente.id] })
      setForm(inicial); setEdicion(null); setMensaje('Borrador guardado. Revísalo antes de publicarlo.')
    } catch (err) {
      const detalle = err.response?.data?.detail
      setError(typeof detalle === 'string' ? detalle : 'No se pudo guardar el borrador. Revisa los datos e inténtalo de nuevo.')
    } finally { setOcupado(false) }
  }

  async function publicar(id) {
    if (ocupado || !window.confirm('¿Confirmas publicar este registro? Desde entonces quedará visible para el equipo médico.')) return
    setOcupado(true); setError(''); setMensaje('')
    try {
      await publicarRegistroEnfermeria(id)
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', paciente.id] })
      setMensaje('Registro publicado. Ya está disponible en la ficha médica del paciente.')
    } catch (err) {
      const detalle = err.response?.data?.detail
      setError(typeof detalle === 'string' ? detalle : 'No se pudo publicar el registro.')
    } finally { setOcupado(false) }
  }

  return <main className="enf-page">
    <header className="enf-topbar"><strong>SarcoSistema · Enfermería</strong><div><span>{usuario.identificador_acceso}</span><Link to="/inicio">Inicio</Link><button onClick={logout}>Cerrar sesión</button></div></header>
    <div className="enf-content">
      <div className="enf-heading"><div><p>ADMISIÓN Y VALORACIÓN INICIAL</p><h1>Registro de enfermería</h1><span>Captura datos referidos y mediciones. Revisa y publica para que el médico pueda consultarlos.</span></div></div>
      <section className="enf-panel">
        <h2>Buscar paciente</h2>
        <label className="enf-search">Nombre, documento, historia clínica o código
          <input type="search" value={entrada} onChange={(event) => setEntrada(event.target.value)} placeholder="Escribe al menos dos caracteres" />
        </label>
        {buscar.length < 2 && <p className="enf-message">Escribe al menos dos caracteres para buscar.</p>}
        {pacientes.isPending && buscar.length >= 2 && <p role="status" className="enf-message">Buscando…</p>}
        {pacientes.isError && <p role="alert" className="enf-message">No se pudo buscar pacientes.</p>}
        {pacientes.data?.items.map((item) => <button className={`enf-patient-option ${paciente?.id === item.id ? 'enf-selected' : ''}`} key={item.id} onClick={() => elegirPaciente(item)}>
          <strong>{item.nombre_completo}</strong><span>HC {item.historia_clinica || 'No registrada'} · {item.codigo_paciente} · {edadPaciente(item.fecha_nacimiento)}</span>
        </button>)}
        {pacientes.data?.total > pacientes.data?.limite && <div className="enf-pagination">
          <button type="button" disabled={pagina === 1} onClick={() => setPagina((valor) => valor - 1)}>Anterior</button>
          <span>Página {pagina} · {pacientes.data.total} resultados</span>
          <button type="button" disabled={pagina * pacientes.data.limite >= pacientes.data.total} onClick={() => setPagina((valor) => valor + 1)}>Siguiente</button>
        </div>}
        {buscar.length >= 2 && pacientes.data?.items.length === 0 && <p className="enf-message">No se encontraron pacientes.</p>}
      </section>

      {paciente && <>
        <section className="enf-panel enf-patient-card"><div><p>PACIENTE SELECCIONADO</p><h2>{paciente.nombre_completo}</h2><span>HC {paciente.historia_clinica || 'No registrada'} · {paciente.codigo_paciente} · {paciente.numero_documento || 'Sin documento'}</span></div></section>
        <section className="enf-panel">
          <div className="enf-panel-heading"><h2>{edicion ? 'Editar borrador' : 'Nueva admisión'}</h2><span>Los campos no medidos pueden dejarse vacíos.</span></div>
          <form className="enf-form" onSubmit={guardar}>
            {narrativas.map(([campo, etiqueta]) => <CampoTexto key={campo} campo={campo} etiqueta={etiqueta} form={form} onChange={(event) => setForm((actual) => ({ ...actual, [campo]: event.target.value }))} />)}
            <fieldset><legend>Mediciones y signos vitales</legend><div className="enf-measurements">
              {mediciones.map(([campo, etiqueta]) => <label key={campo}>{etiqueta}<input type="number" step={campo === 'dolor_escala' ? '1' : 'any'} min="0" value={form[campo]} onChange={(event) => setForm((actual) => ({ ...actual, [campo]: event.target.value }))} placeholder="No registrado" /></label>)}
            </div></fieldset>
            {error && <p role="alert" className="enf-error">{error}</p>}{mensaje && <p role="status" className="enf-message">{mensaje}</p>}
            <div className="enf-actions"><button type="submit" className="primary-button" disabled={ocupado}>{ocupado ? 'Guardando…' : edicion ? 'Guardar cambios del borrador' : 'Guardar borrador'}</button>{edicion && <button type="button" onClick={() => { setEdicion(null); setForm(inicial) }}>Cancelar edición</button>}</div>
          </form>
        </section>
        <section className="enf-panel"><div className="enf-panel-heading"><h2>Registros de enfermería</h2><span>Los borradores solo los ve su autora; publicados, también el médico.</span></div>
          {registros.isPending && <p role="status" className="enf-message">Cargando registros…</p>}
          {registros.isError && <p role="alert" className="enf-message">No se pudieron cargar los registros.</p>}
          {registros.data?.length === 0 && <p className="enf-message">Aún no hay registros de esta cuenta para el paciente.</p>}
          {registros.data?.map((registro) => <RegistroResumen key={registro.id} registro={registro} ocupado={ocupado} onEditar={(item) => { setEdicion(item.id); setForm(valores(item)); setError(''); setMensaje('') }} onPublicar={publicar} />)}
        </section>
      </>}
    </div>
  </main>
}
