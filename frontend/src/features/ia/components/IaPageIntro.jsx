import './IaPageIntro.css'

export default function IaPageIntro() {
  return (
    <>
      <div className="ia-title-row">
        <div>
          <p className="ia-eyebrow">ASISTENCIA EXPERIMENTAL</p>
          <h1>Transcripción de audio</h1>
          <p className="ia-intro">Convierte una grabación en texto para facilitar su revisión.</p>
        </div>
        <span className="ia-view-label">Procesamiento local</span>
      </div>
      <div className="ia-notice" role="note">
        <span className="ia-notice-icon" aria-hidden="true">i</span>
        <p>
          <strong>La transcripción no es un registro clínico.</strong> El texto generado es un borrador y debe ser revisado y confirmado por un profesional. No se guarda ni se publica automáticamente.
        </p>
      </div>
    </>
  )
}
