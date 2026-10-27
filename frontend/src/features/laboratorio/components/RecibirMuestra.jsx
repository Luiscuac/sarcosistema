import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { recibirMuestraSolicitud } from '../api/laboratorioApi.js'
import { agruparPorCategoria } from '../utils/agruparSolicitudes.js'
import './muestras/RecibirMuestra.css'

function mensajeError(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const campo = Array.isArray(item?.loc) ? item.loc.at(-1) : null
      return campo ? `${campo}: ${item.msg}` : item?.msg
    }).filter(Boolean).join(' · ') || 'Revisa los datos de la muestra e inténtalo de nuevo.'
  }
  if (error.response?.status) {
    return `El servidor respondió con el error ${error.response.status}. ${error.message || ''}`.trim()
  }
  if (error.code === 'ERR_NETWORK') {
    return 'No se pudo conectar con el backend. Comprueba que Uvicorn siga ejecutándose.'
  }
  return error.message ? `No se pudo registrar la muestra: ${error.message}` : 'No se pudo registrar la muestra.'
}

function fechaLocal() {
  const hoy = new Date()
  const ajustar = (valor) => String(valor).padStart(2, '0')
  return `${hoy.getFullYear()}-${ajustar(hoy.getMonth() + 1)}-${ajustar(hoy.getDate())}`
}

export default function RecibirMuestra({ solicitud, onClose, onReceived }) {
  const queryClient = useQueryClient()
  const pendientes = solicitud.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra')
  const [estudioIds, setEstudioIds] = useState([])
  const [tipoMuestra, setTipoMuestra] = useState('')
  const [fecha, setFecha] = useState(fechaLocal)
  const [hora, setHora] = useState(new Date().toTimeString().slice(0, 5))
  const [horaNoRegistrada, setHoraNoRegistrada] = useState(false)
  function alternarEstudio(estudioId) {
    setEstudioIds((actuales) => actuales.includes(estudioId)
      ? actuales.filter((id) => id !== estudioId)
      : [...actuales, estudioId])
  }
  const mutation = useMutation({
    mutationFn: () => recibirMuestraSolicitud(solicitud.id, {
      estudio_ids: estudioIds,
      tipo_muestra: tipoMuestra,
      fecha_toma: fecha,
      hora_toma: horaNoRegistrada ? null : hora,
      hora_no_registrada: horaNoRegistrada,
    }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      onReceived()
    },
  })

  return (
    <div className="lab-dialog-backdrop" role="presentation" onMouseDown={(event) => { if (!mutation.isPending && event.target === event.currentTarget) onClose() }}>
      <section className="lab-dialog" role="dialog" aria-modal="true" aria-labelledby="receive-sample-title">
        <header className="lab-dialog-header">
          <div><p className="lab-eyebrow">RECEPCIÓN</p><h2 id="receive-sample-title">Registrar muestra</h2>
            <p>{solicitud.referencia} · {solicitud.paciente_nombre}</p></div>
          <button className="lab-dialog-close" type="button" onClick={onClose} disabled={mutation.isPending} aria-label="Cerrar">×</button>
        </header>
        <form onSubmit={(event) => { event.preventDefault(); mutation.mutate() }}>
          <div className="lab-dialog-body">
            <section className="lab-form-section">
              <h3>Estudios asociados a esta muestra</h3>
              <p className="lab-form-hint">Selecciona únicamente los estudios que usarán esta muestra. Para otra muestra, repite el registro desde la solicitud.</p>
              <div className="lab-sample-study-list">
                {agruparPorCategoria(pendientes).map((categoria) => <fieldset key={categoria.codigo ?? 'otros'} disabled={mutation.isPending}>
                  <legend>{categoria.nombre}</legend>
                  {categoria.estudios.map((estudio) => <label key={estudio.estudio_id}>
                    <input type="checkbox" checked={estudioIds.includes(estudio.estudio_id)} onChange={() => alternarEstudio(estudio.estudio_id)} />
                    {estudio.tipo_estudio_nombre}
                  </label>)}
                </fieldset>)}
              </div>
              {estudioIds.length === 0 && <p className="lab-form-hint">Elige al menos un estudio antes de guardar.</p>}
            </section>
            <section className="lab-form-section">
              <h3>Datos de la muestra</h3>
              <p className="lab-form-hint">Indica cuándo se tomó la muestra. El sistema registra automáticamente cuándo la guardas aquí.</p>
              <div className="lab-form-grid">
                <label>Tipo de muestra
                  <input value={tipoMuestra} onChange={(event) => setTipoMuestra(event.target.value)} disabled={mutation.isPending} required maxLength={120} placeholder="Ej.: sangre, orina o heces" />
                </label>
                <label>Fecha de toma
                  <input type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} disabled={mutation.isPending} required />
                </label>
                <label>Hora de toma
                  <input type="time" value={hora} onChange={(event) => setHora(event.target.value)} disabled={mutation.isPending || horaNoRegistrada} required={!horaNoRegistrada} />
                </label>
                <label className="lab-checkbox-label"><input type="checkbox" checked={horaNoRegistrada} onChange={(event) => setHoraNoRegistrada(event.target.checked)} disabled={mutation.isPending} /> La hora no fue registrada</label>
              </div>
              {mutation.isError && <p className="lab-form-error" role="alert">{mensajeError(mutation.error)}</p>}
            </section>
          </div>
          <footer className="lab-dialog-footer">
            <button type="button" onClick={onClose} disabled={mutation.isPending}>Cancelar</button>
            <button className="primary-button" type="submit" disabled={mutation.isPending || estudioIds.length === 0}>{mutation.isPending ? 'Guardando…' : 'Guardar muestra'}</button>
          </footer>
        </form>
      </section>
    </div>
  )
}
