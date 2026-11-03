import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { recibirMuestraSolicitud, registrarIncidenciasSolicitud } from '../api/laboratorioApi.js'
import { areasParaMuestra } from '../utils/areasMuestra.js'
import './muestras/RecibirMuestra.css'

function mensajeError(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => {
      const campo = Array.isArray(item?.loc) ? item.loc.at(-1) : null
      return campo ? `${campo}: ${item.msg}` : item?.msg
    }).filter(Boolean).join(' · ') || 'Revisa los datos e inténtalo de nuevo.'
  }
  if (error.response?.status) {
    return `El servidor respondió con el error ${error.response.status}. ${error.message || ''}`.trim()
  }
  if (error.code === 'ERR_NETWORK') {
    return 'No se pudo conectar con el backend. Comprueba que Uvicorn siga ejecutándose.'
  }
  return error.message ? `No se pudo guardar: ${error.message}` : 'No se pudo guardar.'
}

function fechaLocal() {
  const hoy = new Date()
  const ajustar = (valor) => String(valor).padStart(2, '0')
  return `${hoy.getFullYear()}-${ajustar(hoy.getMonth() + 1)}-${ajustar(hoy.getDate())}`
}

export default function RecibirMuestra({ solicitud, onClose, onReceived }) {
  const queryClient = useQueryClient()
  const pendientes = solicitud.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra')
  const [areasSeleccionadas, setAreasSeleccionadas] = useState([])
  const [tipoMuestra, setTipoMuestra] = useState('Sangre')
  const [responsable, setResponsable] = useState('')
  const [fecha, setFecha] = useState(fechaLocal)
  const [hora, setHora] = useState(new Date().toTimeString().slice(0, 5))
  const [horaNoRegistrada, setHoraNoRegistrada] = useState(false)
  const [modo, setModo] = useState('muestra')
  const [motivo, setMotivo] = useState('muestra_no_entregada')
  const [descripcion, setDescripcion] = useState('')
  const areas = areasParaMuestra(pendientes, tipoMuestra)
  const estudioIds = areas.filter((area) => areasSeleccionadas.includes(area.codigo))
    .flatMap((area) => area.estudios.map((estudio) => estudio.estudio_id))
  function alternarArea(codigo) {
    setAreasSeleccionadas((actuales) => actuales.includes(codigo)
      ? actuales.filter((item) => item !== codigo) : [...actuales, codigo])
  }
  const mutation = useMutation({
    mutationFn: () => modo === 'incidencia'
      ? registrarIncidenciasSolicitud(solicitud.id, {
        estudio_ids: estudioIds,
        motivo,
        descripcion: descripcion.trim(),
        responsable: responsable.trim(),
      })
      : recibirMuestraSolicitud(solicitud.id, {
        estudio_ids: estudioIds,
        tipo_muestra: tipoMuestra,
        fecha_toma: fecha,
        hora_toma: horaNoRegistrada ? null : hora,
        hora_no_registrada: horaNoRegistrada,
        responsable_recepcion: responsable.trim(),
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
          <div><p className="lab-eyebrow">RECEPCIÓN</p><h2 id="receive-sample-title">{modo === 'incidencia' ? 'Registrar incidencia' : 'Registrar muestra'}</h2>
            <p>{solicitud.referencia} · {solicitud.paciente_nombre}</p></div>
          <button className="lab-dialog-close" type="button" onClick={onClose} disabled={mutation.isPending} aria-label="Cerrar">×</button>
        </header>
        <form onSubmit={(event) => { event.preventDefault(); mutation.mutate() }}>
          <div className="lab-dialog-body">
            <div className="lab-reception-modes" aria-label="Acción de recepción">
              <button type="button" className={modo === 'muestra' ? 'lab-reception-mode is-active' : 'lab-reception-mode'} aria-pressed={modo === 'muestra'} onClick={() => { setModo('muestra'); mutation.reset() }} disabled={mutation.isPending}>Registrar muestra</button>
              <button type="button" className={modo === 'incidencia' ? 'lab-reception-mode is-active is-incidence' : 'lab-reception-mode is-incidence'} aria-pressed={modo === 'incidencia'} onClick={() => { setModo('incidencia'); mutation.reset() }} disabled={mutation.isPending}>Registrar incidencia</button>
            </div>
            <section className="lab-form-section">
              <h3>{modo === 'incidencia' ? 'Áreas afectadas' : 'Áreas asociadas a esta muestra'}</h3>
              <p className="lab-form-hint">Al marcar un área se incluyen todos sus estudios pendientes. Registra orina y heces por separado.{modo === 'incidencia' && ' La constancia se aplicará a las áreas seleccionadas.'}</p>
              <label>Tipo de muestra
                <select value={tipoMuestra} onChange={(event) => { setTipoMuestra(event.target.value); setAreasSeleccionadas([]) }} disabled={mutation.isPending}>
                  <option>Sangre</option><option>Orina</option><option>Heces</option>
                </select>
              </label>
              <div className="lab-sample-study-list">
                {areas.map((area) => <label key={area.codigo}>
                  <input type="checkbox" checked={areasSeleccionadas.includes(area.codigo)} onChange={() => alternarArea(area.codigo)} disabled={mutation.isPending} />
                  {area.codigo === 'hematologia' ? 'Hematología' : area.codigo === 'bioquimica' ? 'Bioquímica' : area.codigo === 'serologia' ? 'Serología' : area.codigo} ({area.estudios.length} estudios)
                </label>)}
              </div>
              {areas.length === 0 && <p className="lab-form-hint">No hay estudios pendientes para esta muestra.</p>}
            </section>
            <section className="lab-form-section">
              <h3>{modo === 'incidencia' ? 'Datos de la incidencia' : 'Datos de la muestra'}</h3>
              {modo === 'incidencia' && <p className="lab-form-hint">Los estudios seleccionados se cerrarán como no realizados y la justificación aparecerá en el informe final.</p>}
              <div className="lab-form-grid">
                <label>{modo === 'incidencia' ? 'Responsable que registra la constancia' : 'Responsable de toma o recepción'}<input required minLength="2" maxLength="200" value={responsable} onChange={(event) => setResponsable(event.target.value)} disabled={mutation.isPending} placeholder="Nombre y apellido" /></label>
                {modo === 'incidencia' ? <>
                  <label>Motivo<select value={motivo} onChange={(event) => setMotivo(event.target.value)} disabled={mutation.isPending}><option value="muestra_no_entregada">Muestra no entregada</option><option value="toma_rechazada">Toma rechazada</option><option value="toma_no_realizada">Toma no realizada</option></select></label>
                  <label className="lab-full-field">Descripción<textarea required minLength="3" maxLength="1000" rows="3" value={descripcion} onChange={(event) => setDescripcion(event.target.value)} disabled={mutation.isPending} placeholder="Explica brevemente lo ocurrido" /></label>
                </> : <>
                  <label>Fecha de toma
                    <input type="date" value={fecha} onChange={(event) => setFecha(event.target.value)} disabled={mutation.isPending} required />
                  </label>
                  <label>Hora de toma
                    <input type="time" value={hora} onChange={(event) => setHora(event.target.value)} disabled={mutation.isPending || horaNoRegistrada} required={!horaNoRegistrada} />
                  </label>
                  <label className="lab-checkbox-label"><input type="checkbox" checked={horaNoRegistrada} onChange={(event) => setHoraNoRegistrada(event.target.checked)} disabled={mutation.isPending} /> La hora no fue registrada</label>
                </>}
              </div>
              {mutation.isError && <p className="lab-form-error" role="alert">{mensajeError(mutation.error)}</p>}
            </section>
          </div>
          <footer className="lab-dialog-footer">
            <button type="button" onClick={onClose} disabled={mutation.isPending}>Cancelar</button>
            <button className={modo === 'incidencia' ? 'lab-incidence-submit' : 'primary-button'} type="submit" disabled={mutation.isPending || estudioIds.length === 0 || (modo === 'incidencia' && (responsable.trim().length < 2 || descripcion.trim().length < 3))}>{mutation.isPending ? 'Guardando…' : modo === 'incidencia' ? 'Registrar incidencia y cerrar' : 'Guardar muestra'}</button>
          </footer>
        </form>
      </section>
    </div>
  )
}
