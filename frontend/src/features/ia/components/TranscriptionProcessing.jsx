import './TranscriptionProcessing.css'

export default function TranscriptionProcessing() {
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
