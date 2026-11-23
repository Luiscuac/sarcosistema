import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { emitirRecetaMedica } from '../api/consultasApi.js'
import { obtenerRecetasPublicadas } from '../../enfermeria/api/enfermeriaApi.js'
import ConfirmarAccion from '../../../shared/ui/ConfirmarAccion.jsx'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import { fecha } from '../utils/paciente.js'
import Boton from '../../../shared/ui/Boton.jsx'
import { fechaHoy, formatearFechaHora } from '../../../shared/utils/formatearFecha.js'

const medicamentoVacio = () => ({ nombre_generico: '', forma_concentracion: '', indicaciones: '', cantidad_recetada: '' })

function fechaReceta(receta) {
  return receta.publicado_en ? formatearFechaHora(receta.publicado_en) : fecha(receta.fecha)
}

function RecetaResumen({ receta, pacienteId }) {
  return <article className="med-history-list-item">
    <div className="med-history-list-main">
      <strong>{receta.numero_receta || `Receta #${receta.id}`}</strong>
      <span>{fechaReceta(receta)}</span>
    </div>
    <p><span>Diagnóstico</span>{receta.diagnostico_principal || 'No indicado'}</p>
    <Link className="med-history-open" to={`/consultas/pacientes/${pacienteId}/recetas/${receta.id}`}>Ver informe <span aria-hidden="true">→</span></Link>
  </article>
}

function InformeReceta({ receta, paciente }) {
  const fechaEmision = fechaReceta(receta)
  return <>
    <header className="med-history-report-header">
      <div>
        <p className="med-eyebrow">INFORME DE RECETA</p>
        <h2>{receta.numero_receta || `Receta #${receta.id}`}</h2>
        <p>Emitida el {fechaEmision}</p>
      </div>
      <Link className="med-prescription-back" to={`/consultas/pacientes/${paciente.id}?seccion=receta`}>Volver a recetas</Link>
    </header>
    <div className="med-history-report">
      <dl className="med-report-meta">
        <div><dt>Paciente</dt><dd>{paciente.nombre_completo}</dd></div>
        <div><dt>Historia clínica</dt><dd>{receta.historia_clinica || paciente.historia_clinica || 'No registrada'}</dd></div>
        <div><dt>Médico prescriptor</dt><dd>{receta.prescriptor || receta.registrado_por || 'No indicado'}</dd></div>
      </dl>
      <section className="med-report-section">
        <h3>Diagnóstico</h3>
        <p>{receta.diagnostico_principal || 'No indicado'}</p>
      </section>
      <section className="med-report-section">
        <h3>Medicamentos prescritos <span>{receta.medicamentos?.length || 0}</span></h3>
        {receta.medicamentos?.length
          ? <ol className="med-report-medications">
            {receta.medicamentos.map((medicamento, indice) => <li key={`${receta.id}-${indice}`}>
              <header><strong>{medicamento.nombre_generico}</strong><span>{medicamento.forma_concentracion}</span></header>
              <p>{medicamento.indicaciones}</p>
              <footer>Cantidad recetada: <strong>{medicamento.cantidad_recetada || 'No especificada'}</strong></footer>
            </li>)}
          </ol>
          : <p className="med-message">La receta no tiene medicamentos registrados.</p>}
      </section>
    </div>
  </>
}

export default function RecetaMedica({ paciente, mode = 'lista', recetaId }) {
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const navigate = useNavigate()
  const [diagnostico, setDiagnostico] = useState('')
  const [medicamentos, setMedicamentos] = useState([medicamentoVacio()])
  const [medicamentoActivo, setMedicamentoActivo] = useState(0)
  const [errorMedicamentos, setErrorMedicamentos] = useState('')
  const [confirmando, setConfirmando] = useState(false)
  const recetas = useQuery({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id],
    queryFn: () => obtenerRecetasPublicadas(paciente.id) })
  const recetaSeleccionada = recetas.data?.find(receta => String(receta.id) === String(recetaId))
  const mutation = useMutation({ mutationFn: datos => emitirRecetaMedica(paciente.id, datos),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id] })
      notificar('Receta emitida y enviada a farmacia.', 'exito')
      navigate(`/consultas/pacientes/${paciente.id}?seccion=receta`, { replace: true })
    },
    onError: () => setConfirmando(false) })
  const actualizar = (i, campo, valor) => {
    setMedicamentos(actual => actual.map((m, n) => n === i ? { ...m, [campo]: valor } : m))
    setErrorMedicamentos('')
  }
  function agregarMedicamento() {
    setMedicamentos(actual => [...actual, medicamentoVacio()])
    setMedicamentoActivo(medicamentos.length)
    setErrorMedicamentos('')
  }
  function quitarMedicamento(indice) {
    const restantes = medicamentos.filter((_, n) => n !== indice)
    setMedicamentos(restantes)
    setMedicamentoActivo(actual => actual > indice ? actual - 1 : Math.min(actual, restantes.length - 1))
    setErrorMedicamentos('')
  }
  function revisar(evento) {
    evento.preventDefault()
    const incompleto = medicamentos.findIndex(m => !m.nombre_generico.trim() || !m.forma_concentracion.trim() || !m.indicaciones.trim())
    if (incompleto !== -1) {
      setMedicamentoActivo(incompleto)
      setErrorMedicamentos(`Completa los campos obligatorios del medicamento ${incompleto + 1} antes de revisar la receta.`)
      return
    }
    setConfirmando(true)
  }
  function emitir() {
    // Fecha de calendario local: con toISOString() las recetas de la noche quedaban con fecha de mañana.
    mutation.mutate({ fecha: fechaHoy(), diagnostico_principal: diagnostico.trim(),
      medicamentos: medicamentos.map(m => ({ ...m, cantidad_dispensada: null, valor_unitario: null, valor_total: null })) })
  }
  return <section className="med-panel">
    {mode === 'nueva'
      ? <>
        <div className="med-prescription-form-header">
          <div>
            <p className="med-eyebrow">NUEVA RECETA</p>
            <h2>Receta para {paciente.nombre_completo}</h2>
            <p>Completa el diagnóstico y los medicamentos; al confirmar, se enviará a farmacia.</p>
          </div>
          <Link className="med-prescription-back" to={`/consultas/pacientes/${paciente.id}?seccion=receta`}>Volver a recetas</Link>
        </div>
        <form className="med-form med-prescription-form" onSubmit={revisar}>
          <div className="med-fields med-fields--single">
            <label><span>Diagnóstico <abbr title="Obligatorio">*</abbr></span>
              <input required maxLength={1000} value={diagnostico} onChange={e => setDiagnostico(e.target.value)} placeholder="Ej.: Faringoamigdalitis aguda" />
            </label>
          </div>
          <div className="med-prescription-meds">
            <h3>Medicamentos <span>{medicamentos.length}</span></h3>
            {errorMedicamentos && <p role="alert" className="med-error">{errorMedicamentos}</p>}
            {medicamentos.map((m, i) => i === medicamentoActivo && <fieldset key={i} className="med-prescription-med" aria-label={`Medicamento ${i + 1}`}>
              <div className="med-prescription-med-heading">
                <strong className="med-prescription-med-title">Medicamento {i + 1}</strong>
                {medicamentos.length > 1 && <button type="button" className="med-secondary-button med-danger-button"
                  onClick={() => quitarMedicamento(i)} aria-label={`Quitar medicamento ${i + 1}`}>Quitar</button>}
              </div>
              <div className="med-fields">
                <label><span>Nombre genérico <abbr title="Obligatorio">*</abbr></span><input required value={m.nombre_generico} onChange={e => actualizar(i, 'nombre_generico', e.target.value)} placeholder="Ej.: Amoxicilina" /></label>
                <label><span>Forma y concentración <abbr title="Obligatorio">*</abbr></span><input required value={m.forma_concentracion} onChange={e => actualizar(i, 'forma_concentracion', e.target.value)} placeholder="Ej.: Cápsula 500 mg" /></label>
                <label className="med-field-wide"><span>Indicaciones (dosis, frecuencia, duración y vía) <abbr title="Obligatorio">*</abbr></span><textarea required rows={2} value={m.indicaciones} onChange={e => actualizar(i, 'indicaciones', e.target.value)} placeholder="Ej.: 1 cápsula cada 8 horas por 10 días, vía oral" /></label>
                <label>Cantidad recetada<input value={m.cantidad_recetada} onChange={e => actualizar(i, 'cantidad_recetada', e.target.value)} placeholder="Ej.: 30 cápsulas" /></label>
              </div>
            </fieldset>)}
            <nav className="med-prescription-steps" aria-label="Medicamentos de la receta">
              <ol>{medicamentos.map((m, i) => {
                const completo = Boolean(m.nombre_generico.trim() && m.forma_concentracion.trim() && m.indicaciones.trim())
                return <li key={i}>
                  <button type="button" className={medicamentoActivo === i ? 'active' : completo ? 'complete' : ''} aria-current={medicamentoActivo === i ? 'step' : undefined}
                    aria-label={`Medicamento ${i + 1}${completo ? ', completo' : ', incompleto'}`} onClick={() => setMedicamentoActivo(i)}>{i + 1}</button>
                </li>
              })}</ol>
            </nav>
            <button type="button" className="med-add-button" onClick={agregarMedicamento}>+ Añadir otro medicamento</button>
          </div>
          {mutation.isError && <p role="alert" className="med-error">No se pudo emitir la receta. Revisa los datos e inténtalo de nuevo.</p>}
          <div className="med-form-actions">
            <Boton type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Emitiendo…' : 'Revisar y emitir…'}</Boton>
          </div>
        </form>
      </>
      : mode === 'detalle'
        ? recetaSeleccionada
          ? <InformeReceta receta={recetaSeleccionada} paciente={paciente} />
          : recetas.isPending
            ? <p role="status" className="med-message">Cargando informe de receta…</p>
            : <p role="alert" className="med-message">No se pudo encontrar el informe de esta receta.</p>
        : <>
        <div className="med-panel-header med-prescription-list-header">
          <div><h2>Recetas emitidas</h2><span>Solo se muestran las recetas enviadas a farmacia.</span></div>
          <Link className="primary-button med-button-link med-add-prescription" to={`/consultas/pacientes/${paciente.id}/recetas/nueva`}>+ Agregar receta</Link>
        </div>
        {recetas.isPending && <p role="status" className="med-message">Cargando recetas…</p>}
        {recetas.isError && <p role="alert" className="med-error med-prescription-load-error">No se pudieron cargar las recetas emitidas.</p>}
        {recetas.data?.length === 0 && <div className="med-prescription-empty">
          <span aria-hidden="true">Rx</span>
          <h3>Aún no hay recetas emitidas</h3>
          <p>Las recetas confirmadas aparecerán aquí.</p>
        </div>}
        {recetas.data?.map(receta => <RecetaResumen key={receta.id} receta={receta} pacienteId={paciente.id} />)}
      </>}

    {confirmando && <ConfirmarAccion titulo="Emitir receta" textoConfirmar="Emitir y enviar a farmacia" textoCancelar="Seguir editando"
      pendiente={mutation.isPending} onCancelar={() => setConfirmando(false)} onConfirmar={emitir}>
      <p>Paciente: <strong>{paciente.nombre_completo}</strong>. Farmacia y enfermería verán la receta en cuanto la emitas; <strong>no se puede editar después</strong>.</p>
      <dl className="med-final-summary"><div><dt>Diagnóstico</dt><dd>{diagnostico}</dd></div></dl>
      <ol className="med-prescription-summary">{medicamentos.map((m, i) => <li key={i}>
        <strong>{m.nombre_generico}</strong> · {m.forma_concentracion}<br />{m.indicaciones}{m.cantidad_recetada && <><br />Cantidad: {m.cantidad_recetada}</>}
      </li>)}</ol>
    </ConfirmarAccion>}
  </section>
}
