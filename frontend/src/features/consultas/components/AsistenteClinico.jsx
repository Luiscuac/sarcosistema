import { useCallback, useEffect, useRef, useState } from 'react'
import useAudioRecorder from '../../ia/hooks/useAudioRecorder.js'
import { transcribirAudio } from '../../ia/whisper/api/iaApi.js'
import { extraerDatosClinicos } from '../api/consultasApi.js'
import { grupos } from '../utils/formulario.js'
import PropuestaCampo from './PropuestaCampo.jsx'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'

const etiquetas = Object.fromEntries(grupos.flatMap(g => g.campos))
const ttl = Math.max(10, Math.min(900, Number(import.meta.env.VITE_CLINICAL_AUDIO_TTL_SECONDS) || 300))
const duracionMaxima = Math.max(10, Math.min(1200, Number(import.meta.env.VITE_CLINICAL_AUDIO_MAX_SECONDS) || 180))

export default function AsistenteClinico({ pacienteId, valores, onAplicar, onDeshacer, onEstado, onRevision }) {
  const recorder = useAudioRecorder()
  const [autorizado, setAutorizado] = useState(false)
  const [fase, setFase] = useState('listo')
  const [original, setOriginal] = useState('')
  const [texto, setTexto] = useState('')
  const [items, setItems] = useState([])
  const [propuesta, setPropuesta] = useState(null)
  const [error, setError] = useState('')
  // Pregunta abierta en un diálogo propio: { titulo, cuerpo, textoConfirmar, accion }.
  const [pregunta, setPregunta] = useState(null)
  const operacion = useRef(0)
  const controlador = useRef(null)
  const procesado = useRef(new WeakSet())
  const recorderRef = useRef(recorder)
  recorderRef.current = recorder
  const ocupado = fase === 'transcribiendo' || fase === 'analizando' || recorder.estado === 'recording' || recorder.estado === 'requesting'
  const procesando = fase === 'transcribiendo' || fase === 'analizando'
  const pendientes = items.some(item => item.estado === 'pendiente')
  const aceptadas = items.map((item, indice) => ({ item, indice })).filter(({ item }) => item.estado === 'aceptada')

  useEffect(() => {
    onEstado({ bloqueado: ocupado || pendientes, hayDatos: Boolean(original || texto || recorder.audio || ocupado) })
  }, [ocupado, pendientes, original, texto, recorder.audio, onEstado])

  useEffect(() => () => {
    operacion.current += 1
    controlador.current?.abort()
  }, [])

  useEffect(() => {
    if (!recorder.audio) return
    const timer = setTimeout(() => {
      operacion.current += 1
      controlador.current?.abort()
      recorderRef.current.cancelarGrabacion()
      setFase('error')
      setError('Se agotó el plazo de conservación en memoria; el audio se descartó. Puedes continuar manualmente.')
    }, ttl * 1000)
    return () => clearTimeout(timer)
  }, [recorder.audio])

  useEffect(() => {
    if (recorder.estado === 'recording' && recorder.segundos >= duracionMaxima) recorder.detenerGrabacion()
  }, [recorder.estado, recorder.segundos, recorder.detenerGrabacion])

  const analizar = useCallback(async (transcripcion, idOperacion, signal) => {
    setFase('analizando')
    const resultado = await extraerDatosClinicos(pacienteId, transcripcion, signal)
    if (signal.aborted || idOperacion !== operacion.current) return
    setPropuesta(resultado)
    setItems(resultado.campos_extraidos.map(item => ({ ...item, estado: 'pendiente' })))
    setFase('revision')
  }, [pacienteId])

  useEffect(() => {
    if (!recorder.audio || procesado.current.has(recorder.audio)) return
    procesado.current.add(recorder.audio)
    const audio = recorder.audio
    const nombre = recorder.nombreAudio
    const idOperacion = ++operacion.current
    controlador.current?.abort()
    const controller = new window.AbortController()
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
        setError('No se pudo transcribir o analizar. Puedes reintentar el análisis del texto o continuar manualmente.')
        setFase('error')
      } finally {
        if (idOperacion === operacion.current) recorderRef.current.limpiarGrabacion()
      }
    }
    procesar()
  }, [recorder.audio, recorder.nombreAudio, analizar])

  function informarRevision(nuevos) {
    if (!propuesta) return
    onRevision({ propuesta_id: propuesta.propuesta_id, modelo: propuesta.modelo,
      campos_aceptados: nuevos.filter(item => item.estado === 'aceptada').map(item => item.campo) })
  }

  function resolver(indice, aceptar, confirmado = false) {
    const item = items[indice]
    let aplicacion
    if (aceptar) {
      aplicacion = onAplicar(item, confirmado)
      if (aplicacion.requiereConfirmacion) {
        setPregunta({
          titulo: `Reemplazar «${etiquetas[item.campo] || item.campo}»`,
          cuerpo: <><p>Este campo ya tiene información escrita a mano. Solo se reemplaza este campo.</p>
            <dl className="med-final-summary"><div><dt>Valor actual</dt><dd>{aplicacion.anterior}</dd></div><div><dt>Propuesta</dt><dd>{String(item.valor)}</dd></div></dl></>,
          textoConfirmar: 'Reemplazar con la propuesta',
          accion: () => resolver(indice, true, true),
        })
        return
      }
      if (!aplicacion.aplicada) return
    }
    const nuevos = items.map((actual, i) => i === indice
      ? { ...actual, estado: aceptar ? 'aceptada' : 'rechazada', anterior: aplicacion?.anterior, revisionAplicacion: aplicacion?.revisionAplicacion } : actual)
    setItems(nuevos)
    informarRevision(nuevos)
  }

  function deshacer(indice) {
    onDeshacer(items[indice])
    const nuevos = items.map((item, i) => i === indice ? { ...item, estado: 'rechazada' } : item)
    setItems(nuevos)
    informarRevision(nuevos)
  }

  function descartarPendientes() {
    const nuevos = items.map(item => item.estado === 'pendiente' ? { ...item, estado: 'rechazada' } : item)
    setItems(nuevos)
    informarRevision(nuevos)
  }

  function cancelar() {
    operacion.current += 1
    controlador.current?.abort()
    recorder.cancelarGrabacion()
    descartarPendientes()
    setFase('listo')
    setError('')
  }

  function reprocesar() {
    if (ocupado || texto.trim().length < 2) return
    if (pendientes) {
      setPregunta({ titulo: 'Volver a analizar', textoConfirmar: 'Descartar pendientes y analizar',
        cuerpo: <p>Se descartan las propuestas que todavía no revisaste. Los campos escritos a mano o ya aceptados se conservan.</p>,
        accion: analizarDeNuevo })
      return
    }
    analizarDeNuevo()
  }

  async function analizarDeNuevo() {
    descartarPendientes()
    const idOperacion = ++operacion.current
    const controller = new window.AbortController()
    controlador.current = controller
    setError('')
    try { await analizar(texto, idOperacion, controller.signal) }
    catch {
      if (controller.signal.aborted || idOperacion !== operacion.current) return
      setError('El extractor no está disponible o no devolvió datos válidos. Continúa manualmente o reintenta.')
      setFase('error')
    }
  }

  function iniciar() {
    if (!autorizado || ocupado) return
    if (pendientes) {
      setPregunta({ titulo: 'Nueva grabación', textoConfirmar: 'Descartar pendientes y grabar',
        cuerpo: <p>Se descartan las propuestas que todavía no revisaste. Los campos ya aceptados se conservan.</p>,
        accion: grabarDeNuevo })
      return
    }
    grabarDeNuevo()
  }

  function grabarDeNuevo() {
    descartarPendientes()
    setPropuesta(null)
    setItems([])
    setOriginal('')
    setTexto('')
    setError('')
    setFase('listo')
    recorder.iniciarGrabacion()
  }

  return <section className="med-panel med-assistant" aria-label="Dictado y propuestas clínicas">
    <p className="med-hint med-assistant-intro">Graba o escribe la consulta; la IA propone campos y tú decides cuáles aplicar.</p>
    <div className="med-capture" aria-label="Formas de ingresar la consulta">
      <div className="med-capture-card med-capture-voice">
        <div className="med-capture-heading"><h3>Dictar</h3></div>
        <button type="button" className={`med-record-button${recorder.estado === 'recording' ? ' med-record-button--active' : ''}`}
          disabled={recorder.estado !== 'recording' && (!autorizado || ocupado)}
          onClick={recorder.estado === 'recording' ? recorder.detenerGrabacion : iniciar}
          aria-label={recorder.estado === 'recording' ? 'Detener grabación' : 'Iniciar grabación'}>
          <svg viewBox="0 0 32 32" fill="none" aria-hidden="true"><rect x="12" y="4" width="8" height="17" rx="4" stroke="currentColor" strokeWidth="2"/><path d="M8 15v2a8 8 0 0 0 16 0v-2M16 25v4m-5 0h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          <span>{recorder.estado === 'recording' ? 'Detener grabación' : recorder.estado === 'requesting' ? 'Activando micrófono…' : 'Iniciar grabación'}</span>
          {recorder.estado === 'recording' && <time>{recorder.tiempo}</time>}
        </button>
        {recorder.estado === 'recording' && <div className="med-input-level" role="status" aria-label={recorder.nivelMicrofono > 4 ? 'Señal de micrófono detectada' : 'No se detecta señal de micrófono'}><span className="med-live-dot" /><span className="med-input-track"><span style={{ width: `${recorder.nivelMicrofono}%` }} /></span><span>{recorder.nivelMicrofono > 4 ? 'Se está escuchando' : 'Comprueba el micrófono'}</span></div>}
        <label className="med-consent"><input type="checkbox" checked={autorizado} disabled={ocupado} onChange={e => setAutorizado(e.target.checked)} />El paciente autorizó grabar esta atención.</label>
        <details className="med-microphone-settings"><summary>Configurar micrófono</summary><div className="med-microphone-picker">
          <label htmlFor="med-microphone-select">Micrófono de entrada</label>
          {recorder.microfonos.length > 0
            ? <select id="med-microphone-select" value={recorder.microfonoId} disabled={ocupado} onChange={e => recorder.setMicrofonoId(e.target.value)}>
              {recorder.microfonos.map((microfono, indice) => <option key={microfono.deviceId || indice} value={microfono.deviceId}>{microfono.label || `Micrófono ${indice + 1}`}</option>)}
            </select>
            : <span className="med-hint">Se usará el micrófono predeterminado.</span>}
          <button type="button" disabled={ocupado || recorder.buscandoMicrofonos} onClick={recorder.buscarMicrofonos}>{recorder.buscandoMicrofonos ? 'Buscando…' : 'Buscar micrófonos'}</button>
        </div></details>
      </div>
      <div className="med-capture-card med-capture-text">
        <div className="med-capture-heading"><h3>Escribir o pegar</h3></div>
        <label className="sr-only" htmlFor="med-analysis-text">Texto para analizar</label>
        <textarea id="med-analysis-text" rows={7} maxLength={12000} placeholder="Escribe aquí el motivo de consulta, síntomas, antecedentes y otros datos…" value={texto} disabled={ocupado} onChange={e => setTexto(e.target.value)} />
        <button type="button" className="med-analyze-button" disabled={ocupado || texto.trim().length < 2} onClick={reprocesar}>Analizar texto</button>
        {original && <span className="med-hint">Puedes corregir la transcripción aquí sin cambiar el original.</span>}
      </div>
      {procesando && <div className="med-processing" role="status" aria-live="polite">
        <span className="med-processing-spinner" aria-hidden="true" />
        <strong>{fase === 'transcribiendo' ? 'Transcribiendo la grabación…' : 'Analizando la consulta…'}</strong>
        <p>{fase === 'transcribiendo' ? 'Estamos convirtiendo el audio en texto.' : 'Estamos preparando los datos para que los revises.'}</p>
        <button type="button" onClick={cancelar}>Cancelar y continuar manualmente</button>
      </div>}
    </div>
    <details className="med-dictation-example"><summary>Ver un ejemplo de dictado</summary><p>La paciente viene porque desde hace tres días tiene dolor de garganta y fiebre por las noches. Dice que le duele al tragar y que tiene tos seca, pero no le falta el aire. De niña tuvo asma leve. Al revisarla tiene la garganta roja con placas blancas. Tiene 38.5 de temperatura y el pulso en 96. Creo que es una amigdalitis bacteriana. Le doy amoxicilina de 500 cada 8 horas por 10 días y que vuelva en tres días.</p><span className="med-hint">Puedes hablar con naturalidad: no hace falta nombrar cada campo. Revisa cada propuesta antes de aplicarla.</span></details>
    {pendientes && <button type="button" className="med-cancel-proposals" onClick={cancelar}>Cancelar propuestas y continuar manualmente</button>}
    {fase === 'revision' && pendientes && <p className="med-process-result" role="status">Propuestas listas para revisar</p>}
    {(error || recorder.error) && <p className="med-error" role="alert">{error || recorder.error}</p>}
    {original && <details className="med-original-transcript"><summary>Ver transcripción original</summary><p className="med-transcript">{original}</p></details>}
    {propuesta?.advertencias.map((aviso, i) => <p key={i} role="status" className="med-ai-warning">{aviso}</p>)}
    {propuesta?.bloqueada && <p role="alert" className="med-error">Autocompletado bloqueado: revisa a qué paciente corresponde el dictado. No se modificó la ficha.</p>}
    {items.map((item, indice) => item.estado === 'pendiente' && <PropuestaCampo
      key={`${propuesta?.propuesta_id}-${item.campo}`} item={item} etiqueta={etiquetas[item.campo] || item.campo}
      valorActual={valores[item.campo]} bloqueada={propuesta?.bloqueada}
      onCambiarValor={valor => setItems(actual => actual.map((s, i) => i === indice ? { ...s, valor } : s))}
      onAceptar={() => resolver(indice, true)} onRechazar={() => resolver(indice, false)} />)}
    {pendientes && <button type="button" onClick={descartarPendientes}>Rechazar todas las pendientes</button>}
    {aceptadas.length > 0 && <details className="med-assistant-history"><summary>Deshacer un campo aplicado</summary>
      <div className="med-assistant-history-list">{aceptadas.map(({ item, indice }) => <div key={`${propuesta?.propuesta_id}-${item.campo}`}>
        <span>{etiquetas[item.campo] || item.campo}</span>
        <button type="button" onClick={() => deshacer(indice)}>Deshacer</button>
      </div>)}</div>
    </details>}
    <details className="med-privacy-note"><summary>Privacidad y límites del dictado</summary>
      <p className="med-hint">El audio queda solo en memoria: se elimina al transcribir o a los {ttl} s, y la grabación dura como máximo {duracionMaxima} s. La transcripción se descarta al salir. Whisper no distingue quién habla ni indica su confianza: revisa ambigüedades y errores.</p>
    </details>
    {pregunta && <ConfirmarAccion titulo={pregunta.titulo} textoConfirmar={pregunta.textoConfirmar} textoCancelar="Volver"
      onCancelar={() => setPregunta(null)} onConfirmar={() => { const { accion } = pregunta; setPregunta(null); accion() }}>
      {pregunta.cuerpo}
    </ConfirmarAccion>}
  </section>
}
