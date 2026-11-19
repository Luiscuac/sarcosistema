import { useCallback, useEffect, useRef, useState } from 'react'
import useAudioRecorder from '../../ia/hooks/useAudioRecorder.js'
import { transcribirAudio } from '../../ia/whisper/api/iaApi.js'
import { extraerHallazgosEcografia } from '../api/ecografiaApi.js'
import { aplicarPropuestaEcografia, deshacerPropuestaEcografia } from '../asistente.js'

const CAMPOS = {
  evaluaciones: 'Hallazgo',
  zona: 'Zona estudiada',
  observaciones: 'Observaciones',
  conclusion: 'Conclusión',
}
const TTL_AUDIO_SEGUNDOS = 180

function claveCampo(item) {
  return item.organo ? `evaluaciones:${item.organo}` : item.campo
}

function valorActual(datos, item) {
  return item.organo ? datos.evaluaciones?.[item.organo] || '' : datos[item.campo] || ''
}

export default function AsistenteEcografia({ estudioId, datos, onAplicar, onEstado }) {
  const recorder = useAudioRecorder()
  const recorderRef = useRef(recorder)
  recorderRef.current = recorder
  const [autorizado, setAutorizado] = useState(false)
  const [texto, setTexto] = useState('')
  const [original, setOriginal] = useState('')
  const [fase, setFase] = useState('listo')
  const [error, setError] = useState('')
  const [propuesta, setPropuesta] = useState(null)
  const [items, setItems] = useState([])
  const operacion = useRef(0)
  const controlador = useRef(null)
  const procesado = useRef(new WeakSet())
  const pendientes = items.some((item) => item.estado === 'pendiente')
  const grabando = recorder.estado === 'recording'
  const ocupado = fase === 'transcribiendo' || fase === 'analizando'
    || grabando || recorder.estado === 'requesting'

  useEffect(() => {
    onEstado({ bloqueado: ocupado || pendientes })
  }, [ocupado, pendientes, onEstado])

  useEffect(() => () => {
    operacion.current += 1
    controlador.current?.abort()
  }, [])

  useEffect(() => {
    if (grabando && recorder.segundos >= TTL_AUDIO_SEGUNDOS) recorder.detenerGrabacion()
  }, [grabando, recorder.segundos])

  const analizar = useCallback(async (transcripcion, idOperacion, signal) => {
    setFase('analizando')
    const resultado = await extraerHallazgosEcografia(estudioId, transcripcion, signal)
    if (signal.aborted || idOperacion !== operacion.current) return
    setPropuesta(resultado)
    setItems(resultado.campos_extraidos.map((item) => ({ ...item, estado: 'pendiente' })))
    setFase(resultado.bloqueada ? 'bloqueado' : 'revision')
  }, [estudioId])

  useEffect(() => {
    if (!recorder.audio || procesado.current.has(recorder.audio)) return
    procesado.current.add(recorder.audio)
    const audio = recorder.audio
    const nombre = recorder.nombreAudio
    const idOperacion = ++operacion.current
    controlador.current?.abort()
    const controller = new AbortController()
    controlador.current = controller
    setFase('transcribiendo')
    setError('')
    async function procesar() {
      try {
        const resultado = await transcribirAudio(audio, nombre, controller.signal)
        if (controller.signal.aborted || idOperacion !== operacion.current) return
        if (!resultado.texto?.trim()) throw new Error('audio-vacio')
        setOriginal(resultado.texto)
        setTexto(resultado.texto)
        recorderRef.current.limpiarGrabacion()
        await analizar(resultado.texto, idOperacion, controller.signal)
      } catch {
        if (controller.signal.aborted || idOperacion !== operacion.current) return
        setError('No se pudo transcribir o analizar. Puedes corregir el texto y reintentar.')
        setFase('error')
      } finally {
        if (idOperacion === operacion.current) recorderRef.current.limpiarGrabacion()
      }
    }
    procesar()
  }, [recorder.audio, recorder.nombreAudio, analizar])

  function iniciarGrabacion() {
    if (!autorizado || ocupado || pendientes) return
    operacion.current += 1
    controlador.current?.abort()
    setItems([])
    setPropuesta(null)
    setOriginal('')
    setTexto('')
    setError('')
    setFase('listo')
    recorder.iniciarGrabacion()
  }

  async function analizarTexto() {
    if (ocupado || pendientes || texto.trim().length < 2) return
    const idOperacion = ++operacion.current
    controlador.current?.abort()
    const controller = new AbortController()
    controlador.current = controller
    setError('')
    try {
      await analizar(texto, idOperacion, controller.signal)
    } catch {
      if (controller.signal.aborted || idOperacion !== operacion.current) return
      setError('El extractor no está disponible. Reintenta o continúa manualmente.')
      setFase('error')
    }
  }

  function cancelar() {
    operacion.current += 1
    controlador.current?.abort()
    recorder.cancelarGrabacion()
    setItems((anteriores) => anteriores.map((item) => item.estado === 'pendiente'
      ? { ...item, estado: 'rechazada' } : item))
    setFase('listo')
    setError('')
  }

  function aceptar(indice) {
    const item = items[indice]
    if (item.ambiguo) return
    const clave = claveCampo(item)
    const yaAplicada = items.some((actual, i) => i !== indice
      && actual.estado === 'aceptada' && claveCampo(actual) === clave)
    if (yaAplicada) return
    const resultado = aplicarPropuestaEcografia(datos, item)
    if (!resultado) return
    onAplicar(resultado.datos)
    setItems((anteriores) => anteriores.map((actual, i) => i === indice
      ? { ...actual, estado: 'aceptada', anterior: resultado.anterior } : actual))
  }

  function rechazar(indice) {
    setItems((anteriores) => anteriores.map((item, i) => i === indice
      ? { ...item, estado: 'rechazada' } : item))
  }

  function deshacer(indice) {
    const item = items[indice]
    const resultado = deshacerPropuestaEcografia(datos, item, item.anterior)
    if (!resultado) {
      setError('No se deshizo la propuesta porque el campo cambió después de aplicarla. Revísalo manualmente.')
      return
    }
    onAplicar(resultado)
    setItems((anteriores) => anteriores.map((actual, i) => i === indice
      ? { ...actual, estado: 'rechazada', anterior: undefined } : actual))
  }

  return <section className="eco-ai" aria-label="Dictado asistido del informe">
    <header className="eco-ai-header">
      <div><p className="lab-eyebrow">ASISTENCIA DE DICTADO</p>
        <h2>Registrar hallazgos con voz o texto</h2>
        <p>Whisper transcribe; Qwen organiza solo lo mencionado en la plantilla de este estudio.</p>
      </div>
      <button type="button" className="lab-secondary-button" disabled={!ocupado && !pendientes} onClick={cancelar}>
        Cancelar proceso
      </button>
    </header>
    <label className="eco-ai-consent">
      <input type="checkbox" checked={autorizado} disabled={ocupado} onChange={(evento) => setAutorizado(evento.target.checked)} />
      El paciente autorizó grabar esta atención.
    </label>
    <div className="eco-ai-capture">
      <button type="button" className={`eco-ai-record${grabando ? ' is-recording' : ''}`}
        disabled={!grabando && (!autorizado || ocupado || pendientes)}
        onClick={grabando ? recorder.detenerGrabacion : iniciarGrabacion}
        aria-label={grabando ? 'Detener grabación' : 'Iniciar grabación'}>
        <svg viewBox="0 0 32 32" fill="none" aria-hidden="true">
          {grabando
            ? <rect x="9" y="9" width="14" height="14" rx="2" fill="currentColor" />
            : <><rect x="12" y="4" width="8" height="17" rx="4" stroke="currentColor" strokeWidth="2" />
                <path d="M8 15v2a8 8 0 0 0 16 0v-2M16 25v4m-5 0h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></>}
        </svg>
        <span>{grabando ? 'Detener grabación' : recorder.estado === 'requesting' ? 'Activando micrófono…' : 'Iniciar grabación'}</span>
        {grabando && <time>{recorder.tiempo}</time>}
      </button>
      {grabando && <div className="eco-ai-level" role="status"
        aria-label={recorder.nivelMicrofono > 4 ? 'Señal de micrófono detectada' : 'No se detecta señal de micrófono'}>
        <span className="eco-ai-live-dot" />
        <span className="eco-ai-track"><span style={{ width: `${recorder.nivelMicrofono}%` }} /></span>
        <span>{recorder.nivelMicrofono > 4 ? 'Se está escuchando' : 'Comprueba el micrófono'}</span>
      </div>}
    </div>
    <details className="eco-ai-microphone">
      <summary>Configurar micrófono</summary>
      <div>
        <label htmlFor="eco-ai-microphone-select">Micrófono de entrada</label>
        {recorder.microfonos.length
          ? <select id="eco-ai-microphone-select" value={recorder.microfonoId} disabled={ocupado}
              onChange={(evento) => recorder.setMicrofonoId(evento.target.value)}>
              {recorder.microfonos.map((microfono, indice) => <option key={microfono.deviceId || indice} value={microfono.deviceId}>
                {microfono.label || `Micrófono ${indice + 1}`}
              </option>)}
            </select>
          : <span>Se usará el micrófono predeterminado.</span>}
        <button type="button" disabled={ocupado || recorder.buscandoMicrofonos} onClick={recorder.buscarMicrofonos}>
          {recorder.buscandoMicrofonos ? 'Buscando…' : 'Buscar micrófonos'}
        </button>
      </div>
    </details>
    <label className="eco-ai-text">
      Transcripción para analizar
      <textarea rows={4} maxLength={12000} value={texto} disabled={ocupado}
        onChange={(evento) => setTexto(evento.target.value)}
        placeholder="También puedes escribir o pegar aquí los hallazgos dictados." />
    </label>
    <div className="eco-ai-controls">
      <button type="button" className="lab-secondary-button" disabled={ocupado || pendientes || texto.trim().length < 2} onClick={analizarTexto}>
        Analizar texto
      </button>
      {original && <span>La transcripción original se conserva abajo para comparar.</span>}
    </div>
    {ocupado && <p className="eco-ai-status" role="status">{fase === 'transcribiendo' ? 'Transcribiendo audio…' : 'Preparando propuestas…'}</p>}
    {(error || recorder.error) && <p className="eco-ai-error" role="alert">{error || recorder.error}</p>}
    {original && <details className="eco-ai-original"><summary>Transcripción original de Whisper</summary><p>{original}</p></details>}
    {propuesta?.bloqueada && <p className="eco-ai-error" role="alert">No se aplicaron propuestas: verifica que el dictado corresponda a un solo paciente y estudio.</p>}
    {propuesta?.advertencias?.length > 0 && <ul className="eco-ai-warnings">{propuesta.advertencias.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul>}
    {items.length > 0 && <div className="eco-ai-proposals">
      {items.map((item, indice) => {
        const clave = claveCampo(item)
        const conflicto = items.some((actual, i) => i !== indice
          && actual.estado === 'aceptada' && claveCampo(actual) === clave)
        const actual = valorActual(datos, item)
        const etiqueta = item.organo || CAMPOS[item.campo] || item.campo
        return <article key={`${item.campo}-${item.organo || ''}-${indice}`} className={`eco-ai-proposal is-${item.estado}${item.ambiguo ? ' is-ambiguous' : ''}`}>
          <header><strong>{etiqueta}</strong><span>{item.estado === 'aceptada' ? 'Aplicada' : item.estado === 'rechazada' ? 'Rechazada' : item.ambiguo ? 'Revisar manualmente' : 'Propuesta'}</span></header>
          {actual && <p className="eco-ai-existing"><strong>Ya registrado:</strong> {actual}</p>}
          <div className="eco-ai-value"><span>Texto sugerido</span><p>{item.valor}</p></div>
          <blockquote><span>Evidencia del dictado</span><q>{item.evidencia}</q></blockquote>
          {item.alertas?.length > 0 && <ul className="eco-ai-warnings">{item.alertas.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul>}
          {item.estado === 'pendiente'
            ? <div className="eco-ai-proposal-actions">
                <button type="button" className="eco-ai-accept" disabled={item.ambiguo || conflicto} onClick={() => aceptar(indice)}>
                  {conflicto ? 'Deshaz la propuesta aplicada' : 'Aceptar en el informe'}
                </button>
                <button type="button" className="eco-ai-reject" onClick={() => rechazar(indice)}>Rechazar</button>
              </div>
            : item.estado === 'aceptada'
              ? <button type="button" className="eco-ai-undo" onClick={() => deshacer(indice)}>Deshacer aplicación</button>
              : null}
        </article>
      })}
    </div>}
  </section>
}
