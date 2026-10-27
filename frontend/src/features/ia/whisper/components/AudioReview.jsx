import './AudioReview.css'

export default function AudioReview({ audioUrl, tiempo, error, onRestart, onTranscribe }) {
  return (
    <section className="ia-stage-card ia-review-screen">
      <p className="ia-stage-eyebrow">GRABACIÓN LISTA</p>
      <h2>Escucha el audio antes de transcribir</h2>
      <p>Comprueba que se escuche tu voz. Si el audio está vacío o muy bajo, vuelve a grabarlo.</p>
      <audio className="ia-audio-preview" controls preload="metadata" src={audioUrl}>Tu navegador no puede reproducir este audio.</audio>
      <span className="ia-stage-footnote">Duración: {tiempo}</span>
      {error && <p className="ia-error" role="alert">{error}</p>}
      <div className="ia-review-actions">
        <button className="ia-secondary-button" type="button" onClick={onRestart}>Grabar otra vez</button>
        <button className="ia-record-button" type="button" onClick={onTranscribe}>Transcribir con Whisper</button>
      </div>
    </section>
  )
}
