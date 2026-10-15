import { useState } from 'react'
import { Link } from 'react-router-dom'
import { listarCamposDestino, listarVentanasDestino, rellenarCamposDestino } from '../api/agenteLocalApi.js'
import './transcriptor.css'

const camposRegistro = [
  { clave: 'codigo', etiqueta: 'Código' },
  { clave: 'nombre', etiqueta: 'Nombre' },
  { clave: 'fecha', etiqueta: 'Fecha' },
  { clave: 'tipo_examen', etiqueta: 'Examen' },
  { clave: 'resultado', etiqueta: 'Resultado' },
  { clave: 'unidad', etiqueta: 'Unidad' },
]

const registrosPrueba = [
  { id: 'demo-001', codigo: 'PA-TEST-001', nombre: 'Paciente de prueba Uno', fecha: '2026-01-15', tipo_examen: 'Hemoglobina', resultado: '13.8', unidad: 'g/dL' },
  { id: 'demo-002', codigo: 'PA-TEST-002', nombre: 'Paciente de prueba Dos', fecha: '2026-01-16', tipo_examen: 'Glucosa', resultado: '92', unidad: 'mg/dL' },
  { id: 'demo-003', codigo: 'PA-TEST-003', nombre: 'Paciente de prueba Tres', fecha: '2026-01-17', tipo_examen: 'Creatinina', resultado: '0.9', unidad: 'mg/dL' },
]

export default function TranscriptorPage({ usuario, logout }) {
  const registros = registrosPrueba
  const [seleccionado, setSeleccionado] = useState(registrosPrueba[0])
  const [error, setError] = useState('')
  const [copiado, setCopiado] = useState(false)
  const [ventanasDestino, setVentanasDestino] = useState([])
  const [ventanaDestino, setVentanaDestino] = useState('')
  const [controlesDestino, setControlesDestino] = useState([])
  const [mapeoDestino, setMapeoDestino] = useState({})
  const [estadoAgente, setEstadoAgente] = useState('Agente local no conectado.')
  const [cargandoDestino, setCargandoDestino] = useState(false)

  async function conectarAgente() {
    setCargandoDestino(true)
    setError('')
    try {
      const ventanas = await listarVentanasDestino()
      setVentanasDestino(ventanas)
      setVentanaDestino('')
      setControlesDestino([])
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
    setMapeoDestino({})
    if (!handle) return
    setCargandoDestino(true)
    setError('')
    try {
      const controles = await listarCamposDestino(handle)
      setControlesDestino(controles.filter((control) => control.configurable && control.habilitado))
      setEstadoAgente('Ventana inspeccionada. Asigna cada dato a un campo editable.')
    } catch (errorAgente) {
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  async function rellenarDestino() {
    const campos = camposRegistro.map(({ clave }) => ({ ...JSON.parse(mapeoDestino[clave]), valor: String(seleccionado[clave]) }))
    setCargandoDestino(true)
    setError('')
    try {
      const resultado = await rellenarCamposDestino(ventanaDestino, campos)
      setEstadoAgente(`${resultado.campos.length} campos rellenados. Revisa la ventana destino antes de guardar.`)
    } catch (errorAgente) {
      setError(errorAgente.message)
    } finally {
      setCargandoDestino(false)
    }
  }

  const mapeoCompleto = camposRegistro.every(({ clave }) => mapeoDestino[clave])
  const idsMapeados = Object.values(mapeoDestino).filter(Boolean)
  const idsMapeadosUnicos = new Set(idsMapeados).size === idsMapeados.length

  async function copiarRegistro() {
    if (!seleccionado) return
    const texto = [seleccionado.codigo, seleccionado.nombre, seleccionado.fecha, seleccionado.tipo_examen, seleccionado.resultado, seleccionado.unidad].join('\t')
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(true)
      window.setTimeout(() => setCopiado(false), 2000)
    } catch {
      setError('El navegador no permitió copiar los campos.')
    }
  }

  return (
    <main className="transcriptor-page">
      <header className="transcriptor-header">
        <div><Link to="/inicio" className="transcriptor-brand">SarcoSistema</Link><span>PRUEBA DE AUTOMATIZACION LOCAL</span></div>
        <div className="transcriptor-session"><span>{usuario?.identificador_acceso}</span><button type="button" onClick={logout}>Cerrar sesión</button></div>
      </header>
      <section className="transcriptor-content">
        <p className="transcriptor-eyebrow">AGENTE LOCAL DE WINDOWS</p>
        <h1>Registros para transcribir</h1>
        <p className="transcriptor-intro">Selecciona un registro y una aplicacion abierta. El agente permite asignar los datos a los campos del programa destino.</p>
        <div className="transcriptor-warning" role="note"><strong>Entorno de prueba.</strong> Estos datos son ficticios y no se consultan ni modifican registros clínicos.</div>
        {error && <p className="transcriptor-error" role="alert">{error}</p>}
        <div className="transcriptor-layout">
          <section className="transcriptor-card" aria-label="Registros disponibles">
            <h2>Registros disponibles</h2>
            <div className="transcriptor-list">
              {registros.map((registro) => (
                <button key={registro.id} type="button" className={`transcriptor-row${seleccionado?.id === registro.id ? ' is-selected' : ''}`} onClick={() => setSeleccionado(registro)} data-testid={`registro-${registro.id}`}>
                  <span><strong>{registro.codigo}</strong><small>{registro.nombre}</small></span><span>{registro.tipo_examen}</span>
                </button>
              ))}
            </div>
          </section>
          <section className="transcriptor-card transcriptor-detail" aria-label="Vista previa para automatización">
            <div className="transcriptor-detail-heading"><h2>Vista previa</h2><span>Registro de prueba</span></div>
            {seleccionado ? <dl>
              <div data-testid="campo-codigo"><dt>Código</dt><dd>{seleccionado.codigo}</dd></div>
              <div data-testid="campo-nombre"><dt>Nombre</dt><dd>{seleccionado.nombre}</dd></div>
              <div data-testid="campo-fecha"><dt>Fecha</dt><dd>{seleccionado.fecha}</dd></div>
              <div data-testid="campo-examen"><dt>Examen</dt><dd>{seleccionado.tipo_examen}</dd></div>
              <div data-testid="campo-resultado"><dt>Resultado</dt><dd>{seleccionado.resultado}</dd></div>
              <div data-testid="campo-unidad"><dt>Unidad</dt><dd>{seleccionado.unidad}</dd></div>
            </dl> : <p>Elige un registro para ver sus campos.</p>}
            <button className="transcriptor-copy" type="button" onClick={copiarRegistro} disabled={!seleccionado}>{copiado ? 'Copiado' : 'Copiar campos'}</button>
            
          </section>
        </div>
        <section className="transcriptor-card transcriptor-agent" aria-label="Agente local">
          <div className="transcriptor-detail-heading"><div><h2>Agente local de Windows</h2><p>Conecta el agente, selecciona la ventana destino y asigna sus campos.</p></div>
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
            {controlesDestino.length === 0 ? <p>No se detectaron campos editables con nombre o identificador accesible en esta ventana.</p> : <>
              <p>Relaciona cada dato del registro con un campo del programa destino:</p>
              {camposRegistro.map(({ clave, etiqueta }) => <label className="transcriptor-agent-field" key={clave}>{etiqueta}
                <select value={mapeoDestino[clave] || ''} onChange={(event) => setMapeoDestino((actual) => ({ ...actual, [clave]: event.target.value }))}>
                  <option value="">Selecciona un campo</option>
                  {controlesDestino.map((control, indice) => {
                    const selector = JSON.stringify({ selector_tipo: 'indice', selector: String(control.indice) })
                    const detalle = control.automation_id ? `AutomationId: ${control.automation_id}` : `Campo editable #${indice + 1}`
                    return <option key={`${control.indice}-${indice}`} value={selector}>{control.nombre || 'Campo editable'} · {detalle}</option>
                  })}
                </select>
              </label>)}
              <p className="transcriptor-footnote">El agente rellenará los campos seleccionados, pero dejará la aplicación abierta para que revises y guardes manualmente.</p>
              <button className="transcriptor-run" type="button" onClick={rellenarDestino} disabled={cargandoDestino || !mapeoCompleto || !idsMapeadosUnicos}>Rellenar campos en la aplicación</button>
            </>}
          </div>}
        </section>
      </section>
    </main>
  )
}







