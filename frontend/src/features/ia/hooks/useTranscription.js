import { useState } from 'react'
import { transcribirAudio } from '../whisper/api/iaApi.js'
import { mensajeDeError } from '../utils/audio.js'

export default function useTranscription({ audio, nombreAudio, onTranscriptionError }) {
  const [texto, setTexto] = useState('')
  const [procesando, setProcesando] = useState(false)
  const [error, setError] = useState('')

  async function transcribir() {
    if (!audio) return
    setError('')
    setProcesando(true)
    try {
      const resultado = await transcribirAudio(audio, nombreAudio)
      const transcripcion = resultado.texto?.trim() ?? ''
      if (!transcripcion) {
        setError('No se detectó voz. Escucha la grabación y comprueba que se oiga con claridad antes de volver a intentarlo.')
        onTranscriptionError()
        return
      }
      setTexto(transcripcion)
    } catch (errorTranscripcion) {
      setError(mensajeDeError(errorTranscripcion))
      onTranscriptionError()
    } finally {
      setProcesando(false)
    }
  }

  function limpiarTranscripcion() {
    setTexto('')
    setError('')
  }

  return { texto, setTexto, error, procesando, transcribir, limpiarTranscripcion }
}
