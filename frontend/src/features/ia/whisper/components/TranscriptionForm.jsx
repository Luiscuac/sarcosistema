import { useEffect, useRef, useState } from 'react'
import { transcribirAudio } from '../api/iaApi.js'

function mensajeDeError(error) {
  if (error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError') {
    return 'No se concedió acceso al micrófono. Permite el acceso en el navegador e inténtalo de nuevo.'
  }
  if (error?.name === 'NotFoundError' || error?.name === 'DevicesNotFoundError') {
    return 'No se encontró un micrófono disponible en este dispositivo.'
  }
  const estado = error.response?.status
  if (estado === 413) return 'La grabación supera el límite de 20 MB.'
  if (estado === 415) return 'El navegador generó un formato de audio que el servidor no admite.'
  if (estado === 503) return 'El modelo local no está disponible o no pudo procesar el audio.'
  if (!error.response && error.name === 'NotSupportedError') return 'Este navegador no permite grabar audio en un formato compatible.'
  if (!error.response) return 'No se pudo conectar con el servidor. Comprueba que el backend esté iniciado.'
  return 'No se pudo transcribir la grabación. Inténtalo de nuevo.'
}

function nombreDeGrabacion(tipo) {
  if (tipo.includes('ogg')) return 'grabacion.ogg'
  if (tipo.includes('mp4')) return 'grabacion.mp4'
  return 'grabacion.webm'
}

function formatoGrabacion() {
  if (typeof MediaRecorder === 'undefined') return ''
  const opciones = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/ogg', 'audio/mp4']
  return opciones.find((tipo) => MediaRecorder.isTypeSupported(tipo)) ?? ''
}

function formatearTiempo(segundos) {
  const minutos = Math.floor(segundos / 60).toString().padStart(2, '0')
  const resto = (segundos % 60).toString().padStart(2, '0')
  return `${minutos}:${resto}`
}

export default function TranscriptionForm() {
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const medidorRef = useRef(null)
  const partesRef = useRef([])
  const audioRef = useRef(null)
  const nombreAudioRef = useRef('grabacion.webm')
  const [pantalla, setPantalla] = useState('ready')
  const [segundos, setSegundos] = useState(0)
  const [texto, setTexto] = useState('')
  const [error, setError] = useState('')
  const [audioUrl, setAudioUrl] = useState('')
  const [microfonos, setMicrofonos] = useState([])
  const [microfonoId, setMicrofonoId] = useState('')
  const [buscandoMicrofonos, setBuscandoMicrofonos] = useState(false)
  const [nivelMicrofono, setNivelMicrofono] = useState(0)

  useEffect(() => {
    if (pantalla !== 'recording') return undefined
    const timer = window.setInterval(() => setSegundos((valor) => valor + 1), 1000)
    return () => window.clearInterval(timer)
  }, [pantalla])

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

  useEffect(() => () => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.onstop = null
      recorderRef.current.stop()
    }
    const medidor = medidorRef.current
    if (medidor) {
      window.cancelAnimationFrame(medidor.frame)
      medidor.origen.disconnect()
      medidor.context.close()
      medidorRef.current = null
    }
    streamRef.current?.getTracks().forEach((pista) => pista.stop())
  }, [])

  function detenerMedidor() {
    const medidor = medidorRef.current
    if (!medidor) return
    window.cancelAnimationFrame(medidor.frame)
    medidor.origen.disconnect()
    medidor.context.close()
    medidorRef.current = null
  }

  function iniciarMedidor(stream) {
    const AudioContextLocal = window.AudioContext || window.webkitAudioContext
    if (!AudioContextLocal) return
    try {
      const context = new AudioContextLocal()
      const analyser = context.createAnalyser()
      analyser.fftSize = 512
      const origen = context.createMediaStreamSource(stream)
      origen.connect(analyser)
      const muestras = new Uint8Array(analyser.fftSize)
      const medidor = { context, origen, frame: 0 }
      let cuadros = 0
      const actualizar = () => {
        analyser.getByteTimeDomainData(muestras)
        const rms = Math.sqrt(muestras.reduce((suma, valor) => suma + (valor - 128) ** 2, 0) / muestras.length)
        if (cuadros % 6 === 0) setNivelMicrofono(Math.min(100, Math.round(rms * 3)))
        cuadros += 1
        medidor.frame = window.requestAnimationFrame(actualizar)
      }
      medidorRef.current = medidor
      context.resume().then(actualizar).catch(() => {})
    } catch {
      // La grabación sigue disponible aunque el navegador no permita medir el nivel.
    }
  }

  async function actualizarListaMicrofonos() {
    if (!navigator.mediaDevices?.enumerateDevices) {
      setError('Este navegador no permite consultar los micrófonos disponibles.')
      return
    }
    setError('')
    setBuscandoMicrofonos(true)
    let streamTemporal
    try {
      // Obtener acceso primero hace que el navegador revele los nombres de los dispositivos.
      streamTemporal = await navigator.mediaDevices.getUserMedia({ audio: true })
      const dispositivos = await navigator.mediaDevices.enumerateDevices()
      const entradas = dispositivos.filter((dispositivo) => dispositivo.kind === 'audioinput')
      setMicrofonos(entradas)
      const entradaActual = streamTemporal.getAudioTracks()[0]?.getSettings().deviceId
      setMicrofonoId((actual) => entradas.some((entrada) => entrada.deviceId === actual)
        ? actual
        : (entradaActual || entradas[0]?.deviceId || ''))
      if (entradas.length === 0) setError('El navegador no encontró entradas de micrófono.')
    } catch (errorMicrofono) {
      setError(mensajeDeError(errorMicrofono))
    } finally {
      streamTemporal?.getTracks().forEach((pista) => pista.stop())
      setBuscandoMicrofonos(false)
    }
  }

  async function iniciarGrabacion() {
    setError('')
    setTexto('')
    setSegundos(0)
    audioRef.current = null
    setAudioUrl('')
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError('Este navegador no permite grabar audio. Prueba con una versión reciente de Chrome, Edge, Firefox o Safari.')
      return
    }

    try {
      const restriccionesAudio = microfonoId ? { deviceId: { exact: microfonoId } } : true
      const stream = await navigator.mediaDevices.getUserMedia({ audio: restriccionesAudio })
      streamRef.current = stream
      iniciarMedidor(stream)
      const dispositivoEnUso = stream.getAudioTracks()[0]?.getSettings().deviceId
      if (dispositivoEnUso) setMicrofonoId(dispositivoEnUso)
      const tipo = formatoGrabacion()
      const recorder = tipo ? new MediaRecorder(stream, { mimeType: tipo }) : new MediaRecorder(stream)
      partesRef.current = []
      recorderRef.current = recorder
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) partesRef.current.push(event.data)
      }
      recorder.onerror = () => {
        detenerMedidor()
        setNivelMicrofono(0)
        stream.getTracks().forEach((pista) => pista.stop())
        streamRef.current = null
        setError('Ocurrió un problema al grabar el audio. Comprueba el micrófono e inténtalo de nuevo.')
        setPantalla('ready')
      }
      recorder.onstop = () => {
        detenerMedidor()
        setNivelMicrofono(0)
        stream.getTracks().forEach((pista) => pista.stop())
        streamRef.current = null
        const tipoAudio = recorder.mimeType || partesRef.current[0]?.type || 'audio/webm'
        const audio = new Blob(partesRef.current, { type: tipoAudio })
        partesRef.current = []
        if (!audio.size) {
          setError('La grabación quedó vacía. Vuelve a intentarlo y habla cerca del micrófono.')
          setPantalla('ready')
          return
        }
        if (audio.size > 20 * 1024 * 1024) {
          setError('La grabación supera el límite de 20 MB. Haz una grabación más corta.')
          setPantalla('ready')
          return
        }
        audioRef.current = audio
        nombreAudioRef.current = nombreDeGrabacion(tipoAudio)
        setAudioUrl(URL.createObjectURL(audio))
        setPantalla('review')
      }
      recorder.start()
      setPantalla('recording')
    } catch (recordingError) {
      streamRef.current?.getTracks().forEach((pista) => pista.stop())
      streamRef.current = null
      setError(mensajeDeError(recordingError))
      setPantalla('ready')
    }
  }

  function detenerGrabacion() {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.stop()
    }
  }

  async function transcribirGrabacion() {
    if (!audioRef.current) return
    setError('')
    setPantalla('processing')
    try {
      const resultado = await transcribirAudio(audioRef.current, nombreAudioRef.current)
      const transcripcion = resultado.texto?.trim() ?? ''
      if (!transcripcion) {
        setError('No se detectó voz. Escucha la grabación y comprueba que se oiga con claridad antes de volver a intentarlo.')
        setPantalla('review')
        return
      }
      setTexto(transcripcion)
      setPantalla('result')
    } catch (transcriptionError) {
      setError(mensajeDeError(transcriptionError))
      setPantalla('review')
    }
  }

  function nuevaGrabacion() {
    setError('')
    setTexto('')
    setSegundos(0)
    audioRef.current = null
    setAudioUrl('')
    setPantalla('ready')
  }

  if (pantalla === 'processing') {
    return (
      <section className="ia-stage-card ia-processing-screen" aria-live="polite" aria-busy="true">
        <span className="ia-processing-mark" aria-hidden="true"><span /></span>
        <p className="ia-stage-eyebrow">PROCESAMIENTO LOCAL</p>
        <h2>Transcribiendo grabación</h2>
        <p>Whisper está convirtiendo el audio en texto. Puedes dejar esta pantalla abierta mientras termina.</p>
        <span className="ia-stage-footnote">La primera solicitud puede tardar mientras se carga el modelo.</span>
      </section>
    )
  }

  if (pantalla === 'result') {
    return (
      <section className="ia-result-screen">
        <div className="ia-result-topline">
          <div><p className="ia-stage-eyebrow">TRANSCRIPCIÓN COMPLETADA</p><h2>Revisa el texto</h2></div>
          <span className="ia-complete-badge"><span aria-hidden="true">✓</span> Lista para revisar</span>
        </div>
        <textarea className="ia-transcription" value={texto} onChange={(event) => setTexto(event.target.value)} aria-label="Texto transcrito editable" />
        <div className="ia-result-bottom">
          <p className="ia-review-note"><span aria-hidden="true">i</span> Borrador generado con IA. Requiere revisión y confirmación profesional.</p>
          <button className="ia-secondary-button" type="button" onClick={nuevaGrabacion}>Grabar otra vez</button>
        </div>
      </section>
    )
  }

  if (pantalla === 'review') {
    return (
      <section className="ia-stage-card ia-review-screen">
        <p className="ia-stage-eyebrow">GRABACIÓN LISTA</p>
        <h2>Escucha el audio antes de transcribir</h2>
        <p>Comprueba que se escuche tu voz. Si el audio está vacío o muy bajo, vuelve a grabarlo.</p>
        <audio className="ia-audio-preview" controls preload="metadata" src={audioUrl}>
          Tu navegador no puede reproducir este audio.
        </audio>
        <span className="ia-stage-footnote">Duración: {formatearTiempo(segundos)}</span>
        {error && <p className="ia-error" role="alert">{error}</p>}
        <div className="ia-review-actions">
          <button className="ia-secondary-button" type="button" onClick={nuevaGrabacion}>Grabar otra vez</button>
          <button className="ia-record-button" type="button" onClick={transcribirGrabacion}>Transcribir con Whisper</button>
        </div>
      </section>
    )
  }

  return (
    <section className={`ia-stage-card${pantalla === 'recording' ? ' ia-recording-screen' : ''}`}>
      {pantalla === 'recording' ? (
        <>
          <div className="ia-live-indicator"><span /> GRABANDO</div>
          <div className="ia-microphone ia-microphone--active" aria-hidden="true">●</div>
          <h2>Te estamos escuchando</h2>
          <p>Habla con claridad. El indicador mostrará si el micrófono está recibiendo sonido.</p>
          <div className="ia-input-level" role="status" aria-label={nivelMicrofono > 4 ? 'Señal de micrófono detectada' : 'No se detecta señal de micrófono'}>
            <span className="ia-input-level-track"><span style={{ width: `${nivelMicrofono}%` }} /></span>
            <span>{nivelMicrofono > 4 ? 'Señal de micrófono detectada' : 'Habla para comprobar el micrófono'}</span>
          </div>
          <div className="ia-timer" aria-live="off">{formatearTiempo(segundos)}</div>
          <button className="ia-record-button ia-record-button--stop" type="button" onClick={detenerGrabacion}>
            <span aria-hidden="true" /> Detener grabación
          </button>
        </>
      ) : (
        <>
          <p className="ia-stage-eyebrow">DICTADO POR VOZ</p>
          <div className="ia-microphone" aria-hidden="true">●</div>
          <h2>Graba tu audio</h2>
          <p>Presiona el botón para comenzar. Al terminar, podrás escuchar el audio antes de enviarlo a Whisper.</p>
          <div className="ia-microphone-picker">
            <label htmlFor="ia-microphone-select">Micrófono de entrada</label>
            {microfonos.length > 0 ? (
              <select id="ia-microphone-select" value={microfonoId} onChange={(event) => setMicrofonoId(event.target.value)}>
                {microfonos.map((microfono, indice) => (
                  <option key={microfono.deviceId || indice} value={microfono.deviceId}>
                    {microfono.label || `Micrófono ${indice + 1}`}
                  </option>
                ))}
              </select>
            ) : (
              <span className="ia-microphone-hint">Se usará el micrófono predeterminado del navegador.</span>
            )}
            <button className="ia-secondary-button" type="button" onClick={actualizarListaMicrofonos} disabled={buscandoMicrofonos}>
              {buscandoMicrofonos ? 'Buscando…' : 'Buscar micrófonos'}
            </button>
          </div>
          <button className="ia-record-button" type="button" onClick={iniciarGrabacion}>
            <span aria-hidden="true" /> Iniciar grabación
          </button>
          <span className="ia-stage-footnote">Necesitarás permitir el acceso al micrófono en tu navegador.</span>
          {error && <p className="ia-error" role="alert">{error}</p>}
        </>
      )}
    </section>
  )
}
