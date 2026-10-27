import { useEffect, useRef, useState } from 'react'
import { formatearTiempo, mensajeDeError } from '../utils/audio.js'

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

export default function useAudioRecorder() {
  const recorderRef = useRef(null)
  const streamRef = useRef(null)
  const medidorRef = useRef(null)
  const partesRef = useRef([])
  const [estado, setEstado] = useState('ready')
  const [segundos, setSegundos] = useState(0)
  const [audio, setAudio] = useState(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [nombreAudio, setNombreAudio] = useState('grabacion.webm')
  const [microfonos, setMicrofonos] = useState([])
  const [microfonoId, setMicrofonoId] = useState('')
  const [buscandoMicrofonos, setBuscandoMicrofonos] = useState(false)
  const [nivelMicrofono, setNivelMicrofono] = useState(0)
  const [error, setError] = useState('')

  useEffect(() => {
    if (estado !== 'recording') return undefined
    const timer = window.setInterval(() => setSegundos((valor) => valor + 1), 1000)
    return () => window.clearInterval(timer)
  }, [estado])

  useEffect(() => () => {
    if (audioUrl) URL.revokeObjectURL(audioUrl)
  }, [audioUrl])

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
      // La grabación funciona aunque no se pueda medir el nivel de entrada.
    }
  }

  async function buscarMicrofonos() {
    if (!navigator.mediaDevices?.enumerateDevices) {
      setError('Este navegador no permite consultar los micrófonos disponibles.')
      return
    }
    setError('')
    setBuscandoMicrofonos(true)
    let streamTemporal
    try {
      streamTemporal = await navigator.mediaDevices.getUserMedia({ audio: true })
      const dispositivos = await navigator.mediaDevices.enumerateDevices()
      const entradas = dispositivos.filter((dispositivo) => dispositivo.kind === 'audioinput')
      setMicrofonos(entradas)
      const entradaActual = streamTemporal.getAudioTracks()[0]?.getSettings().deviceId
      setMicrofonoId((actual) => entradas.some((entrada) => entrada.deviceId === actual)
        ? actual
        : (entradaActual || entradas[0]?.deviceId || ''))
      if (!entradas.length) setError('El navegador no encontró entradas de micrófono.')
    } catch (errorMicrofono) {
      setError(mensajeDeError(errorMicrofono))
    } finally {
      streamTemporal?.getTracks().forEach((pista) => pista.stop())
      setBuscandoMicrofonos(false)
    }
  }

  async function iniciarGrabacion() {
    setError('')
    setSegundos(0)
    setAudio(null)
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
        setEstado('ready')
      }
      recorder.onstop = () => {
        detenerMedidor()
        setNivelMicrofono(0)
        stream.getTracks().forEach((pista) => pista.stop())
        streamRef.current = null
        const tipoAudio = recorder.mimeType || partesRef.current[0]?.type || 'audio/webm'
        const grabacion = new Blob(partesRef.current, { type: tipoAudio })
        partesRef.current = []
        if (!grabacion.size) {
          setError('La grabación quedó vacía. Vuelve a intentarlo y habla cerca del micrófono.')
          setEstado('ready')
          return
        }
        if (grabacion.size > 20 * 1024 * 1024) {
          setError('La grabación supera el límite de 20 MB. Haz una grabación más corta.')
          setEstado('ready')
          return
        }
        setAudio(grabacion)
        setNombreAudio(nombreDeGrabacion(tipoAudio))
        setAudioUrl(URL.createObjectURL(grabacion))
        setEstado('review')
      }
      recorder.start()
      setEstado('recording')
    } catch (errorGrabacion) {
      streamRef.current?.getTracks().forEach((pista) => pista.stop())
      streamRef.current = null
      setError(mensajeDeError(errorGrabacion))
      setEstado('ready')
    }
  }

  function detenerGrabacion() {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }

  function limpiarGrabacion() {
    setError('')
    setSegundos(0)
    setAudio(null)
    setAudioUrl('')
    setEstado('ready')
  }

  useEffect(() => () => {
    if (recorderRef.current?.state === 'recording') {
      recorderRef.current.onstop = null
      recorderRef.current.stop()
    }
    detenerMedidor()
    streamRef.current?.getTracks().forEach((pista) => pista.stop())
  }, [])

  return {
    estado, setEstado, segundos, tiempo: formatearTiempo(segundos), audio, audioUrl,
    nombreAudio, microfonos, microfonoId, setMicrofonoId, buscandoMicrofonos,
    nivelMicrofono, error, setError, buscarMicrofonos, iniciarGrabacion,
    detenerGrabacion, limpiarGrabacion,
  }
}
