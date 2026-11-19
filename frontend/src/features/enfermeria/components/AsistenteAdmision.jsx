import { useCallback, useEffect, useRef, useState } from 'react'
import useAudioRecorder from '../../ia/hooks/useAudioRecorder.js'
import { transcribirAudio } from '../../ia/whisper/api/iaApi.js'
import { extraerDatosAdmision } from '../api/enfermeriaApi.js'
import { ETIQUETAS_PROPUESA_ADMISION, parchesAdmision, textoPropuesta } from '../utils/asistenteAdmision.js'

export default function AsistenteAdmision({ pacienteId, form, onCambiar, onEstado }) {
  const recorder = useAudioRecorder()
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
  const ocupado = fase === 'transcribiendo' || fase === 'analizando'
    || recorder.estado === 'recording' || recorder.estado === 'requesting'

  useEffect(() => {
    onEstado?.({ bloqueado: ocupado || pendientes, hayDatos: Boolean(texto || recorder.audio || ocupado || pendientes) })
  }, [ocupado, pendientes, texto, recorder.audio, onEstado])

  useEffect(() => () => {
    operacion.current += 1
    controlador.current?.abort()
  }, [])

  const analizar = useCallback(async (transcripcion, idOperacion, signal) => {
    setFase('analizando')
    const resultado = await extraerDatosAdmision(pacienteId, transcripcion, signal)
    if (signal.aborted || idOperacion !== operacion.current) return
    setPropuesta(resultado)
    setItems(resultado.campos_extraidos.map((item) => ({ ...item, estado: 'pendiente' })))
    setFase(resultado.bloqueada ? 'bloqueado' : 'revision')
  }, [pacienteId])

  useEffect(() => {
    if (!recorder.audio || procesado.current.has(recorder.audio)) return
    procesado.current.add(recorder.audio)
    const idOperacion = ++operacion.current
    controlador.current?.abort()
    const controller = new AbortController()
    controlador.current = controller
    setFase('transcribiendo')
    setError('')
    const procesar = async () => {
      try {
        const resultado = await transcribirAudio(recorder.audio, recorder.nombreAudio, controller.signal)
        if (controller.signal.aborted || idOperacion !== operacion.current) return
        if (!resultado.texto?.trim()) throw new Error('audio-vacio')
        setOriginal(resultado.texto)
        setTexto(resultado.texto)
        recorder.limpiarGrabacion()
        await analizar(resultado.texto, idOperacion, controller.signal)
      } catch {
        if (controller.signal.aborted || idOperacion !== operacion.current) return
        setError('No se pudo transcribir o analizar. Puedes continuar manualmente.')
        setFase('error')
      } finally {
        if (idOperacion === operacion.current) recorder.limpiarGrabacion()
      }
    }
    procesar()
  }, [recorder.audio, recorder.nombreAudio, recorder.limpiarGrabacion, analizar])

  async function analizarTexto() {
    if (ocupado || texto.trim().length < 2) return
    const idOperacion = ++operacion.current
    controlador.current?.abort()
    const controller = new AbortController()
    controlador.current = controller
    setError('')
    try {
      await analizar(texto, idOperacion, controller.signal)
    } catch {
      if (controller.signal.aborted || idOperacion !== operacion.current) return
      setError('El extractor no está disponible. Reinténtalo o continúa manualmente.')
      setFase('error')
    }
  }

  function cancelar() {
    operacion.current += 1
    controlador.current?.abort()
    recorder.cancelarGrabacion()
    setFase('listo')
    setError('')
  }

  function aceptar(indice) {
    const item = items[indice]
    const parches = parchesAdmision(item, form)
    if (!parches) return
    const anterior = Object.fromEntries(Object.keys(parches).map((campo) => [campo, form[campo] ?? '']))
    const nuevos = items.map((actual, i) => i === indice
      ? { ...actual, estado: 'aceptada', anterior } : actual)
    Object.entries(parches).forEach(([campo, valor]) => onCambiar(campo, valor))
    setItems(nuevos)
  }

  function rechazar(indice) {
    setItems((actuales) => actuales.map((item, i) => i === indice ? { ...item, estado: 'rechazada' } : item))
  }

  function deshacer(indice) {
    const item = items[indice]
    if (item.anterior) Object.entries(item.anterior).forEach(([campo, valor]) => onCambiar(campo, valor))
    setItems((actuales) => actuales.map((actual, i) => i === indice ? { ...actual, estado: 'rechazada', anterior: undefined } : actual))
  }

  return <section className="enf-ai-panel" aria-label="Dictado asistido de admisión">
    <div className="enf-ai-heading">
      <div><strong>Dictado asistido</strong><span>Whisper local + revisión antes de aplicar</span></div>
      <button type="button" className="enf-ai-cancel" disabled={!ocupado && !pendientes} onClick={cancelar}>Cancelar</button>
    </div>
    <label className="enf-ai-consent">
      <input type="checkbox" checked={autorizado} disabled={ocupado} onChange={(evento) => setAutorizado(evento.target.checked)} />
      El paciente autorizó grabar esta atención.
    </label>
    <div className="enf-ai-actions">
      <button type="button" disabled={!autorizado || ocupado || pendientes} onClick={recorder.estado === 'recording' ? recorder.detenerGrabacion : recorder.iniciarGrabacion}>
        {recorder.estado === 'recording' ? 'Detener grabación' : 'Iniciar grabación'}
      </button>
      {recorder.estado === 'recording' && <span role="status">{recorder.tiempo}</span>}
    </div>
    <label className="enf-ai-text">
      Texto para analizar
      <textarea rows={3} maxLength={12000} value={texto} disabled={ocupado} onChange={(evento) => setTexto(evento.target.value)}
        placeholder="Puede pegar o escribir el motivo, síntomas, observaciones y signos vitales…" />
    </label>
    <button type="button" className="enf-ai-analyze" disabled={ocupado || pendientes || texto.trim().length < 2} onClick={analizarTexto}>
      Analizar texto
    </button>
    {(ocupado) && <p role="status" className="enf-ai-status">{fase === 'transcribiendo' ? 'Transcribiendo…' : 'Analizando…'}</p>}
    {error && <p role="alert" className="enf-ai-error">{error}</p>}
    {original && <details><summary>Ver transcripción original</summary><p>{original}</p></details>}
    {propuesta?.bloqueada && <p role="alert" className="enf-ai-error">El dictado parece referirse a más de un paciente o la identidad no está clara. No se aplicó ningún dato.</p>}
    {propuesta?.advertencias?.length > 0 && <ul className="enf-ai-warnings">{propuesta.advertencias.map((aviso) => <li key={aviso}>{aviso}</li>)}</ul>}
    {items.length > 0 && <div className="enf-ai-proposals">
      {items.map((item, indice) => <article key={`${item.campo}-${indice}`} className={`enf-ai-proposal is-${item.estado}`}>
        <div><strong>{ETIQUETAS_PROPUESA_ADMISION[item.campo] || item.campo}</strong><span>{textoPropuesta(item)}</span></div>
        <p><span>Evidencia:</span> {item.evidencia}</p>
        {item.alertas?.length > 0 && <small>{item.alertas.join(' ')}</small>}
        {item.estado === 'pendiente'
          ? <div className="enf-ai-proposal-actions">
              <button type="button" onClick={() => aceptar(indice)}>Aceptar</button>
              <button type="button" onClick={() => rechazar(indice)}>Rechazar</button>
            </div>
          : item.estado === 'aceptada'
            ? <button type="button" className="enf-ai-undo" onClick={() => deshacer(indice)}>Deshacer</button>
            : <span className="enf-ai-rejected">Rechazada</span>}
      </article>)}
    </div>}
  </section>
}
