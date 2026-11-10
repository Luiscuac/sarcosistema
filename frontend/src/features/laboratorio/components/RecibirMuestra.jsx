import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { recibirMuestraSolicitud, registrarIncidenciasSolicitud } from '../api/laboratorioApi.js'
import ConfirmarAccion from './ConfirmarAccion.jsx'
import Dialogo from './Dialogo.jsx'
import { useResponsableRecordado } from '../hooks/useResponsableRecordado.js'
import { areasParaMuestra } from '../utils/areasMuestra.js'
import { MOTIVOS_INCIDENCIA, nombreArea, nombreMotivoIncidencia } from '../utils/catalogos.js'
import { mensajeError } from '../utils/mensajeError.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import './muestras/RecibirMuestra.css'

const TIPOS_MUESTRA = ['Sangre', 'Orina', 'Heces']

const fechaDeHoy = () => new Date().toLocaleDateString('en-CA')
const horaActual = () => new Date().toTimeString().slice(0, 5)

export default function RecibirMuestra({ solicitud, usuario, onClose, onReceived }) {
  const queryClient = useQueryClient()
  const { notificar } = useNotificacion()
  const { recordado, recordar } = useResponsableRecordado(usuario)
  const pendientes = solicitud.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra')
  const [modo, setModo] = useState('muestra')
  const [tipoMuestra, setTipoMuestra] = useState('Sangre')
  const [areasSeleccionadas, setAreasSeleccionadas] = useState([])
  const [responsable, setResponsable] = useState(recordado)
  const [fecha, setFecha] = useState(fechaDeHoy)
  const [hora, setHora] = useState(horaActual)
  const [horaNoRegistrada, setHoraNoRegistrada] = useState(false)
  const [motivo, setMotivo] = useState(MOTIVOS_INCIDENCIA[0].codigo)
  const [descripcion, setDescripcion] = useState('')
  const [confirmandoIncidencia, setConfirmandoIncidencia] = useState(false)

  const esIncidencia = modo === 'incidencia'
  const areas = areasParaMuestra(pendientes, tipoMuestra)
  const estudiosElegidos = areas.filter((area) => areasSeleccionadas.includes(area.codigo)).flatMap((area) => area.estudios)
  const estudioIds = estudiosElegidos.map((estudio) => estudio.estudio_id)
  const datosCompletos = estudioIds.length > 0 && responsable.trim().length >= 2 && (!esIncidencia || descripcion.trim().length >= 3)

  const mutation = useMutation({
    mutationFn: () => (esIncidencia
      ? registrarIncidenciasSolicitud(solicitud.id, { estudio_ids: estudioIds, motivo, descripcion: descripcion.trim(), responsable: responsable.trim() })
      : recibirMuestraSolicitud(solicitud.id, {
        estudio_ids: estudioIds,
        tipo_muestra: tipoMuestra,
        fecha_toma: fecha,
        hora_toma: horaNoRegistrada ? null : hora,
        hora_no_registrada: horaNoRegistrada,
        responsable_recepcion: responsable.trim(),
      })),
    onSuccess: async () => {
      recordar(responsable)
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      notificar(esIncidencia
        ? `Incidencia registrada: ${estudioIds.length} ${estudioIds.length === 1 ? 'estudio cerrado' : 'estudios cerrados'} como no realizados.`
        : `Muestra de ${tipoMuestra.toLocaleLowerCase()} registrada. Ya puedes capturar los resultados.`, 'exito')
      onReceived()
    },
    onError: () => setConfirmandoIncidencia(false),
  })

  function cambiarModo(nuevo) {
    setModo(nuevo)
    mutation.reset()
  }

  function alternarArea(codigo) {
    setAreasSeleccionadas((actuales) => (actuales.includes(codigo) ? actuales.filter((item) => item !== codigo) : [...actuales, codigo]))
  }

  function enviar(evento) {
    evento.preventDefault()
    if (esIncidencia) setConfirmandoIncidencia(true)
    else mutation.mutate()
  }

  return <>
    <Dialogo eyebrow="RECEPCIÓN" titulo={esIncidencia ? 'Registrar incidencia' : 'Registrar muestra'}
      descripcion={`${solicitud.referencia} · ${solicitud.paciente_nombre}`} onCerrar={onClose} bloqueado={mutation.isPending}>
      <form onSubmit={enviar}>
        <div className="lab-dialog-body">
          <div className="lab-reception-modes" role="group" aria-label="Acción de recepción">
            <button type="button" className={esIncidencia ? 'lab-reception-mode' : 'lab-reception-mode is-active'} aria-pressed={!esIncidencia}
              onClick={() => cambiarModo('muestra')} disabled={mutation.isPending}>Se recibió la muestra</button>
            <button type="button" className={esIncidencia ? 'lab-reception-mode is-active is-incidence' : 'lab-reception-mode is-incidence'} aria-pressed={esIncidencia}
              onClick={() => cambiarModo('incidencia')} disabled={mutation.isPending}>No se pudo tomar o recibir</button>
          </div>
          <section className="lab-form-section">
            <h3>{esIncidencia ? '1. Áreas afectadas' : '1. ¿Qué muestra llegó?'}</h3>
            <div className="lab-sample-types" role="radiogroup" aria-label="Tipo de muestra">
              {TIPOS_MUESTRA.map((tipo) => <label key={tipo} className={tipo === tipoMuestra ? 'lab-sample-type is-active' : 'lab-sample-type'}>
                <input type="radio" name="tipo-muestra" value={tipo} checked={tipo === tipoMuestra} disabled={mutation.isPending}
                  onChange={() => { setTipoMuestra(tipo); setAreasSeleccionadas([]) }} />{tipo}
              </label>)}
            </div>
            <p className="lab-form-hint">Marca las áreas que se procesarán con esta muestra; se incluyen todos sus estudios pendientes.</p>
            <div className="lab-sample-study-list">
              {areas.map((area) => <label key={area.codigo}>
                <input type="checkbox" checked={areasSeleccionadas.includes(area.codigo)} onChange={() => alternarArea(area.codigo)} disabled={mutation.isPending} />
                <span><strong>{nombreArea(area.codigo)}</strong> · {area.estudios.map((estudio) => estudio.tipo_estudio_nombre).join(', ')}</span>
              </label>)}
            </div>
            {areas.length === 0 && <p className="lab-form-hint">No hay estudios pendientes que usen {tipoMuestra.toLocaleLowerCase()}.</p>}
          </section>
          <section className="lab-form-section">
            <h3>{esIncidencia ? '2. Datos de la incidencia' : '2. Datos de la toma'}</h3>
            {esIncidencia && <p className="lab-form-hint">Los estudios seleccionados se cerrarán como no realizados y la justificación aparecerá en el informe final.</p>}
            <div className="lab-form-grid">
              <label>{esIncidencia ? 'Responsable que registra la constancia' : 'Responsable de toma o recepción'}
                <input required minLength="2" maxLength="200" value={responsable} onChange={(evento) => setResponsable(evento.target.value)} disabled={mutation.isPending} placeholder="Nombre y apellido" />
              </label>
              {esIncidencia ? <>
                <label>Motivo<select value={motivo} onChange={(evento) => setMotivo(evento.target.value)} disabled={mutation.isPending}>
                  {MOTIVOS_INCIDENCIA.map(({ codigo, nombre }) => <option key={codigo} value={codigo}>{nombre}</option>)}
                </select></label>
                <label className="lab-full-field">Descripción<textarea required minLength="3" maxLength="1000" rows="3" value={descripcion} onChange={(evento) => setDescripcion(evento.target.value)} disabled={mutation.isPending} placeholder="Explica brevemente lo ocurrido" /></label>
              </> : <>
                <label>Fecha de toma
                  <input type="date" max={fechaDeHoy()} value={fecha} onChange={(evento) => setFecha(evento.target.value)} disabled={mutation.isPending} required />
                </label>
                <label>Hora de toma
                  <input type="time" value={hora} onChange={(evento) => setHora(evento.target.value)} disabled={mutation.isPending || horaNoRegistrada} required={!horaNoRegistrada} />
                </label>
                <label className="lab-checkbox-label"><input type="checkbox" checked={horaNoRegistrada} onChange={(evento) => setHoraNoRegistrada(evento.target.checked)} disabled={mutation.isPending} /> La hora no fue registrada</label>
              </>}
            </div>
            {mutation.isError && <p className="lab-form-error" role="alert">{mensajeError(mutation.error, 'No se pudo guardar. Inténtalo de nuevo.')}</p>}
          </section>
        </div>
        <footer className="lab-dialog-footer">
          <p className="lab-dialog-summary">{estudioIds.length} {estudioIds.length === 1 ? 'estudio seleccionado' : 'estudios seleccionados'}</p>
          <button type="button" onClick={onClose} disabled={mutation.isPending}>Cancelar</button>
          <button className={esIncidencia ? 'lab-incidence-submit' : 'primary-button'} type="submit" disabled={mutation.isPending || !datosCompletos}>
            {mutation.isPending ? 'Guardando…' : esIncidencia ? 'Registrar incidencia…' : 'Guardar muestra'}
          </button>
        </footer>
      </form>
    </Dialogo>
    {confirmandoIncidencia && <ConfirmarAccion titulo="¿Cerrar estudios como no realizados?" textoConfirmar="Sí, registrar incidencia" peligro
      pendiente={mutation.isPending} onConfirmar={() => mutation.mutate()} onCancelar={() => setConfirmandoIncidencia(false)}>
      <p>Se cerrarán <strong>{estudioIds.length} {estudioIds.length === 1 ? 'estudio' : 'estudios'}</strong> por «{nombreMotivoIncidencia(motivo)}». Esta acción no se puede deshacer:</p>
      <ul>{estudiosElegidos.map((estudio) => <li key={estudio.estudio_id}>{estudio.tipo_estudio_nombre}</li>)}</ul>
    </ConfirmarAccion>}
  </>
}
