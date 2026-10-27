import './TranscriptionResult.css'

export default function TranscriptionResult({ texto, onChange, onRestart }) {
  return (
    <section className="ia-result-screen">
      <div className="ia-result-topline">
        <div><p className="ia-stage-eyebrow">TRANSCRIPCIÓN COMPLETADA</p><h2>Revisa el texto</h2></div>
        <span className="ia-complete-badge"><span aria-hidden="true">✓</span> Lista para revisar</span>
      </div>
      <textarea className="ia-transcription" value={texto} onChange={(event) => onChange(event.target.value)} aria-label="Texto transcrito editable" />
      <div className="ia-result-bottom">
        <p className="ia-review-note"><span aria-hidden="true">i</span> Borrador generado con IA. Requiere revisión y confirmación profesional.</p>
        <button className="ia-secondary-button" type="button" onClick={onRestart}>Grabar otra vez</button>
      </div>
    </section>
  )
}
