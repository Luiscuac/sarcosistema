import AudioCaptureStage from './AudioCaptureStage.jsx'
import AudioReview from './AudioReview.jsx'
import TranscriptionProcessing from './TranscriptionProcessing.jsx'
import TranscriptionResult from './TranscriptionResult.jsx'
import useAudioRecorder from '../../hooks/useAudioRecorder.js'
import useTranscription from '../../hooks/useTranscription.js'
import './TranscriptionForm.css'

export default function TranscriptionForm() {
  const recorder = useAudioRecorder()
  const transcription = useTranscription({
    audio: recorder.audio,
    nombreAudio: recorder.nombreAudio,
    onTranscriptionError: () => recorder.setEstado('review'),
  })

  function iniciarNuevaGrabacion() {
    recorder.limpiarGrabacion()
    transcription.limpiarTranscripcion()
  }

  if (transcription.procesando) return <TranscriptionProcessing />

  if (transcription.texto) {
    return (
      <TranscriptionResult
        texto={transcription.texto}
        onChange={transcription.setTexto}
        onRestart={iniciarNuevaGrabacion}
      />
    )
  }

  if (recorder.estado === 'review') {
    return (
      <AudioReview
        audioUrl={recorder.audioUrl}
        tiempo={recorder.tiempo}
        error={transcription.error}
        onRestart={iniciarNuevaGrabacion}
        onTranscribe={transcription.transcribir}
      />
    )
  }

  return (
    <AudioCaptureStage
      recording={recorder.estado === 'recording'}
      seconds={recorder.tiempo}
      level={recorder.nivelMicrofono}
      microphones={recorder.microfonos}
      microphoneId={recorder.microfonoId}
      onMicrophoneChange={recorder.setMicrofonoId}
      searching={recorder.buscandoMicrofonos}
      error={recorder.error}
      onSearch={recorder.buscarMicrofonos}
      onStart={recorder.iniciarGrabacion}
      onStop={recorder.detenerGrabacion}
    />
  )
}
