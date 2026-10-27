import './AudioCaptureStage.css'

export default function AudioCaptureStage({
  recording, seconds, level, microphones, microphoneId, onMicrophoneChange,
  searching, error, onSearch, onStart, onStop,
}) {
  return (
    <section className={`ia-stage-card${recording ? ' ia-recording-screen' : ''}`}>
      {recording ? (
        <>
          <div className="ia-live-indicator"><span /> GRABANDO</div>
          <div className="ia-microphone ia-microphone--active" aria-hidden="true">●</div>
          <h2>Te estamos escuchando</h2>
          <p>Habla con claridad. El indicador mostrará si el micrófono está recibiendo sonido.</p>
          <div className="ia-input-level" role="status" aria-label={level > 4 ? 'Señal de micrófono detectada' : 'No se detecta señal de micrófono'}>
            <span className="ia-input-level-track"><span style={{ width: `${level}%` }} /></span>
            <span>{level > 4 ? 'Señal de micrófono detectada' : 'Habla para comprobar el micrófono'}</span>
          </div>
          <div className="ia-timer" aria-live="off">{seconds}</div>
          <button className="ia-record-button ia-record-button--stop" type="button" onClick={onStop}>
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
            {microphones.length > 0 ? (
              <select id="ia-microphone-select" value={microphoneId} onChange={(event) => onMicrophoneChange(event.target.value)}>
                {microphones.map((microphone, index) => (
                  <option key={microphone.deviceId || index} value={microphone.deviceId}>
                    {microphone.label || `Micrófono ${index + 1}`}
                  </option>
                ))}
              </select>
            ) : <span className="ia-microphone-hint">Se usará el micrófono predeterminado del navegador.</span>}
            <button className="ia-secondary-button" type="button" onClick={onSearch} disabled={searching}>
              {searching ? 'Buscando…' : 'Buscar micrófonos'}
            </button>
          </div>
          <button className="ia-record-button" type="button" onClick={onStart}>
            <span aria-hidden="true" /> Iniciar grabación
          </button>
          <span className="ia-stage-footnote">Necesitarás permitir el acceso al micrófono en tu navegador.</span>
          {error && <p className="ia-error" role="alert">{error}</p>}
        </>
      )}
    </section>
  )
}
