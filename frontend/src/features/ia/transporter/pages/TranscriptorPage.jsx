import { useState } from 'react'
import { Link } from 'react-router-dom'
import { buscarPacientes, obtenerHistorial } from '../../../consultas/api/consultasApi.js'
import {
  guardarConsultaDestino,
  listarBotonesGuardarConsulta,
  listarCamposDestino,
  listarVentanasDestino,
  rellenarCamposDestino,
} from '../api/agenteLocalApi.js'
import './transcriptor.css'

const camposRegistro = [
  { clave: 'medico_nombre', etiqueta: 'Profesional de salud' },
  { clave: 'peso_kg', etiqueta: 'Peso (kg)' },
  { clave: 'talla_cm', etiqueta: 'Talla (cm)' },
  { clave: 'temperatura_c', etiqueta: 'Temperatura (°C)' },
  { clave: 'frecuencia_cardiaca', etiqueta: 'Frecuencia cardíaca (lat/min)' },
  { clave: 'frecuencia_respiratoria', etiqueta: 'Frecuencia respiratoria (resp/min)' },
  { clave: 'presion_sistolica', etiqueta: 'Presión sistólica (mmHg)' },
  { clave: 'presion_diastolica', etiqueta: 'Presión diastólica (mmHg)' },
  { clave: 'saturacion_oxigeno', etiqueta: 'Saturación de oxígeno (%)' },
  { clave: 'motivo_consulta', etiqueta: 'Motivo de consulta' },
  { clave: 'sintomas', etiqueta: 'Síntomas' },
  { clave: 'enfermedad_actual', etiqueta: 'Enfermedad actual' },
  { clave: 'antecedentes', etiqueta: 'Antecedentes relevantes' },
  { clave: 'examen_fisico', etiqueta: 'Examen físico' },
  { clave: 'hallazgos', etiqueta: 'Hallazgos clínicos' },
  { clave: 'observaciones', etiqueta: 'Observaciones' },
  { clave: 'evaluacion_clinica', etiqueta: 'Evaluación clínica' },
  { clave: 'diagnostico_principal', etiqueta: 'Diagnóstico principal' },
  { clave: 'diagnosticos_secundarios', etiqueta: 'Diagnósticos secundarios' },
  { clave: 'tratamiento', etiqueta: 'Tratamiento' },
  { clave: 'medicamentos', etiqueta: 'Medicamentos indicados' },
  { clave: 'indicaciones', etiqueta: 'Indicaciones médicas' },
  { clave: 'estudios_solicitados', etiqueta: 'Estudios complementarios solicitados' },
  { clave: 'referencias', etiqueta: 'Referencias y contrarreferencias' },
  { clave: 'recomendaciones', etiqueta: 'Recomendaciones' },
  { clave: 'plan_seguimiento', etiqueta: 'Seguimiento o próxima revisión' },
]

export default function TranscriptorPage({ usuario, logout }) {
  const [buscar, setBuscar] = useState('')
  const [pacientes, setPacientes] = useState([])
  const [paciente, setPaciente] = useState(null)
  const [consultas, setConsultas] = useState([])
  const [seleccionado, setSeleccionado] = useState(null)
  const [buscandoPacientes, setBuscandoPacientes] = useState(false)
  const [error, setError] = useState('')
  const [ventanasDestino, setVentanasDestino] = useState([])
  const [ventanaDestino, setVentanaDestino] = useState('')
  const [controlesDestino, setControlesDestino] = useState([])
  const [botonesGuardar, setBotonesGuardar] = useState([])
  const [botonGuardar, setBotonGuardar] = useState('')
  const [rellenoListo, setRellenoListo] = useState(false)
  const [mapeoDestino, setMapeoDestino] = useState({})
  const [estadoAgente, setEstadoAgente] = useState('Agente local no conectado.')
  const [cargandoDestino, setCargandoDestino] = useState(false)

  async function buscarPacientesSistema(evento) {
    evento.preventDefault()
    if (buscar.trim().length < 2) {
      setError('Escribe al menos dos caracteres para buscar un paciente.')
      return
    }
    setBuscandoPacientes(true)
    setError('')
    setPacientes([])
    setPaciente(null)
    setConsultas([])
    setSeleccionado(null)
    setRellenoListo(false)
    try {
      const resultado = await buscarPacientes(buscar.trim())
      setPacientes(resultado.items)
    } catch (errorBusqueda) {
      setError(errorBusqueda.response?.data?.detail || 'No se pudieron buscar pacientes. Comprueba tu sesión médica.')
    } finally {
      setBuscandoPacientes(false)
    }
  }

  async function seleccionarPacienteSistema(item) {
    setPaciente(item)
    setConsultas([])
    setSeleccionado(null)
    setRellenoListo(false)
    setError('')
    setBuscandoPacientes(true)
    try {
      const historial = await obtenerHistorial(item.id)
      setConsultas(historial.items)
    } catch (errorHistorial) {
      setError(errorHistorial.response?.data?.detail || 'No se pudo cargar el historial de consultas.')
    } finally {
      setBuscandoPacientes(false)
    }
  }

  async function conectarAgente() {
    setCargandoDestino(true)
    setError('')
    try {
      const ventanas = await listarVentanasDestino()
      setVentanasDestino(ventanas)
      setVentanaDestino('')
      setControlesDestino([])
      setBotonesGuardar([])
      setBotonGuardar('')
      setRellenoListo(false)
      setMapeoDestino({})
      setEstadoAgente(ventanas.length ? `Agente conectado. ${ventanas.length} ventanas disponibles.` : 'Agente conectado; no se encontraron ventanas visibles.')
    } catch (errorAgente) {
      setEstadoAgente('')
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  async function seleccionarVentana(handle) {
    setVentanaDestino(handle)
    setControlesDestino([])
    setBotonesGuardar([])
    setBotonGuardar('')
    setRellenoListo(false)
    setMapeoDestino({})
    if (!handle) return
    setCargandoDestino(true)
    setError('')
    try {
      const [controles, botones] = await Promise.all([
        listarCamposDestino(handle),
        listarBotonesGuardarConsulta(handle),
      ])
      setControlesDestino(controles.filter((control) => control.configurable && control.habilitado))
      setBotonesGuardar(botones.filter((boton) => boton.habilitado))
      setEstadoAgente('Ventana inspeccionada. Asigna los campos médicos y el botón para guardar la consulta.')
    } catch (errorAgente) {
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  async function rellenarDestino() {
    const campos = camposRegistro.map(({ clave }) => ({ ...JSON.parse(mapeoDestino[clave]), valor: String(seleccionado[clave] ?? '') }))
    setCargandoDestino(true)
    setError('')
    try {
      const resultado = await rellenarCamposDestino(ventanaDestino, campos)
      setRellenoListo(true)
      setEstadoAgente(`${resultado.campos.length} campos de consulta rellenados. Revisa la ventana y luego guarda la consulta.`)
    } catch (errorAgente) {
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  async function guardarEnDestino() {
    if (!window.confirm(`SarcoSistema: ${paciente.nombre_completo} (HC ${paciente.historia_clinica || 'sin historia'}). Confirma que el destino muestra al mismo paciente y los datos correctos. ¿Activar ${botonGuardar}?`)) return
    setCargandoDestino(true)
    setError('')
    try {
      const resultado = await guardarConsultaDestino(ventanaDestino, botonGuardar)
      setEstadoAgente(`Se activó «${resultado.boton}» en la ventana destino.`)
    } catch (errorAgente) {
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  const mapeoCompleto = camposRegistro.every(({ clave }) => mapeoDestino[clave])
  const idsMapeados = Object.values(mapeoDestino).filter(Boolean)
  const idsMapeadosUnicos = new Set(idsMapeados).size === idsMapeados.length

  return (
    <main className="transcriptor-page">
      <header className="transcriptor-header">
        <div><Link to="/inicio" className="transcriptor-brand">SarcoSistema</Link><span>PRUEBA DE AUTOMATIZACIÓN LOCAL</span></div>
        <div className="transcriptor-session"><span>{usuario?.identificador_acceso}</span><button type="button" onClick={logout}>Cerrar sesión</button></div>
      </header>
      <section className="transcriptor-content">
        <p className="transcriptor-eyebrow">AGENTE LOCAL DE WINDOWS · CONSULTA EXTERNA</p>
        <h1>Transporte de consulta médica</h1>
        <p className="transcriptor-intro">Busca un paciente, elige una consulta existente, relaciona sus campos con el formulario abierto y activa el guardado de consulta en la ventana destino.</p>
        <div className="transcriptor-warning" role="note"><strong>Datos clínicos.</strong> Se leen consultas existentes de SarcoSistema. Confirma la identidad del paciente y revisa todos los valores en el destino antes de guardarlos.</div>
        {error && <p className="transcriptor-error" role="alert">{error}</p>}
        <div className="transcriptor-layout">
          <section className="transcriptor-card" aria-label="Consultas disponibles">
            <h2>Buscar paciente</h2>
            <form className="transcriptor-search" onSubmit={buscarPacientesSistema}>
              <input aria-label="Nombre, código o historia clínica" value={buscar} onChange={(evento) => setBuscar(evento.target.value)} placeholder="Nombre, código o historia clínica" />
              <button className="transcriptor-run" type="submit" disabled={buscandoPacientes}>{buscandoPacientes ? 'Buscando…' : 'Buscar'}</button>
            </form>
            <div className="transcriptor-list">
              {pacientes.map((item) => (
                <button key={item.id} type="button" className={`transcriptor-row${paciente?.id === item.id ? ' is-selected' : ''}`} onClick={() => seleccionarPacienteSistema(item)}>
                  <span><strong>{item.nombre_completo}</strong><small>HC {item.historia_clinica || 'Sin historia'} · {item.codigo_paciente}</small></span><span>{item.sexo}</span>
                </button>
              ))}
            </div>
            {paciente && <><h2 className="transcriptor-subheading">Historial de {paciente.nombre_completo}</h2>
              <div className="transcriptor-list">
                {consultas.map((consulta) => (
                  <button key={consulta.id} type="button" className={`transcriptor-row${seleccionado?.id === consulta.id ? ' is-selected' : ''}`} onClick={() => { setSeleccionado(consulta); setRellenoListo(false) }}>
                    <span><strong>{consulta.motivo_consulta}</strong><small>{new Date(consulta.fecha_hora_inicio).toLocaleString('es-BO')} · {consulta.medico_nombre}</small></span><span>{consulta.diagnostico_principal || 'Sin diagnóstico'}</span>
                  </button>
                ))}
                {!buscandoPacientes && consultas.length === 0 && <p>Este paciente no tiene consultas disponibles.</p>}
              </div>
            </>}
          </section>
          <section className="transcriptor-card transcriptor-detail" aria-label="Vista previa de consulta">
            <div className="transcriptor-detail-heading"><h2>Vista previa</h2><span>Solo lectura</span></div>
            {seleccionado ? <><dl>
              <div><dt>Paciente</dt><dd>{paciente.nombre_completo} · HC {paciente.historia_clinica || 'Sin historia'}</dd></div>
              {camposRegistro.map(({ clave, etiqueta }) => <div key={clave}><dt>{etiqueta}</dt><dd>{seleccionado[clave] ?? '—'}</dd></div>)}
            </dl></> : <p>Busca y selecciona un paciente y una consulta de su historial.</p>}
          </section>
        </div>
        <section className="transcriptor-card transcriptor-agent" aria-label="Agente local">
          <div className="transcriptor-detail-heading"><div><h2>Agente local de Windows</h2><p>Selecciona el formulario de consulta abierto y configura sus campos y su botón de guardado.</p></div>
            <button className="transcriptor-run" type="button" onClick={conectarAgente} disabled={cargandoDestino}>{cargandoDestino ? 'Conectando...' : 'Conectar y detectar ventanas'}</button>
          </div>
          <p className="transcriptor-agent-status" role="status">{estadoAgente}</p>
          {ventanasDestino.length > 0 && <label className="transcriptor-agent-field">Ventana destino
            <select value={ventanaDestino} onChange={(event) => seleccionarVentana(event.target.value)}>
              <option value="">Selecciona una aplicación abierta</option>
              {ventanasDestino.map((ventana) => <option key={ventana.handle} value={ventana.handle}>{ventana.titulo}</option>)}
            </select>
          </label>}
          {ventanaDestino && <div className="transcriptor-mapping">
            {controlesDestino.length === 0 ? <p>No se detectaron campos editables identificables en esta ventana.</p> : <>
              <p>Asigna los campos de la consulta al formulario destino. Cada campo debe tener un destino único:</p>
              {camposRegistro.map(({ clave, etiqueta }) => <label className="transcriptor-agent-field" key={clave}>{etiqueta}
                <select value={mapeoDestino[clave] || ''} onChange={(event) => { setMapeoDestino((actual) => ({ ...actual, [clave]: event.target.value })); setRellenoListo(false) }}>
                  <option value="">Selecciona un campo destino</option>
                  {controlesDestino.map((control, indice) => {
                    const selector = JSON.stringify({ selector_tipo: 'indice', selector: String(control.indice) })
                    const detalle = control.automation_id ? `AutomationId: ${control.automation_id}` : `Campo editable #${indice + 1}`
                    return <option key={`${control.indice}-${indice}`} value={selector}>{control.nombre || 'Campo editable'} · {detalle}</option>
                  })}
                </select>
              </label>)}
              <button className="transcriptor-run" type="button" onClick={rellenarDestino} disabled={cargandoDestino || !seleccionado || !mapeoCompleto || !idsMapeadosUnicos}>Rellenar consulta médica</button>
            </>}
            <label className="transcriptor-agent-field">Botón de guardado de consulta
              <select value={botonGuardar} onChange={(event) => setBotonGuardar(event.target.value)}>
                <option value="">Selecciona el botón del destino</option>
                {botonesGuardar.map((boton) => <option key={boton.nombre} value={boton.nombre}>{boton.nombre}</option>)}
              </select>
            </label>
            {botonesGuardar.length === 0 && <p>No se encontró un botón habilitado cuyo nombre indique guardar o finalizar una consulta.</p>}
            <p className="transcriptor-footnote">El botón de guardado solo se habilita si su nombre identifica una acción de consulta. Revisa paciente y datos antes de continuar.</p>
            <button className="transcriptor-run" type="button" onClick={guardarEnDestino} disabled={cargandoDestino || !seleccionado || !rellenoListo || !botonGuardar}>Guardar consulta en el destino</button>
          </div>}
        </section>
      </section>
    </main>
  )
}
