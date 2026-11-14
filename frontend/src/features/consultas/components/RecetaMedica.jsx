import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { emitirRecetaMedica } from '../api/consultasApi.js'
import { obtenerRecetasPublicadas } from '../../enfermeria/api/enfermeriaApi.js'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import { fechaLocalDe } from '../utils/paciente.js'
import RecetaFicha from '../../enfermeria/components/RecetaFicha.jsx'

const medicamentoVacio = () => ({ nombre_generico: '', forma_concentracion: '', indicaciones: '', cantidad_recetada: '' })

export default function RecetaMedica({ paciente }) {
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const [diagnostico, setDiagnostico] = useState('')
  const [medicamentos, setMedicamentos] = useState([medicamentoVacio()])
  const [confirmando, setConfirmando] = useState(false)
  const recetas = useQuery({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id],
    queryFn: () => obtenerRecetasPublicadas(paciente.id) })
  const mutation = useMutation({ mutationFn: datos => emitirRecetaMedica(paciente.id, datos),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id] })
      setDiagnostico(''); setMedicamentos([medicamentoVacio()]); setConfirmando(false)
      notificar('Receta emitida y enviada a farmacia.', 'exito')
    },
    onError: () => setConfirmando(false) })
  const actualizar = (i, campo, valor) => setMedicamentos(actual => actual.map((m, n) => n === i ? { ...m, [campo]: valor } : m))
  function revisar(evento) {
    evento.preventDefault() // los campos `required` ya validaron; antes de enviar a farmacia se confirma
    setConfirmando(true)
  }
  function emitir() {
    // Fecha de calendario local: con toISOString() las recetas de la noche quedaban con fecha de mañana.
    mutation.mutate({ fecha: fechaLocalDe(), diagnostico_principal: diagnostico.trim(),
      medicamentos: medicamentos.map(m => ({ ...m, cantidad_dispensada: null, valor_unitario: null, valor_total: null })) })
  }
  return <section className="med-panel">
    <div className="med-panel-header"><h2>Receta médica</h2><span>Al emitirla, farmacia recibe la receta.</span></div>
    <form className="med-form med-prescription-form" onSubmit={revisar}>
      <div className="med-fields med-fields--single">
        <label><span>Diagnóstico <abbr title="Obligatorio">*</abbr></span>
          <input required maxLength={1000} value={diagnostico} onChange={e => setDiagnostico(e.target.value)} placeholder="Ej.: Faringoamigdalitis aguda" />
        </label>
      </div>
      <div className="med-prescription-meds">
        <h3>Medicamentos <span>{medicamentos.length}</span></h3>
        {medicamentos.map((m, i) => <fieldset key={i} className="med-prescription-med" aria-label={`Medicamento ${i + 1}`}>
          <div className="med-prescription-med-heading">
            <strong className="med-prescription-med-title">Medicamento {i + 1}</strong>
            {medicamentos.length > 1 && <button type="button" className="med-secondary-button med-danger-button"
              onClick={() => setMedicamentos(actual => actual.filter((_, n) => n !== i))} aria-label={`Quitar medicamento ${i + 1}`}>Quitar</button>}
          </div>
          <div className="med-fields">
            <label><span>Nombre genérico <abbr title="Obligatorio">*</abbr></span><input required value={m.nombre_generico} onChange={e => actualizar(i, 'nombre_generico', e.target.value)} placeholder="Ej.: Amoxicilina" /></label>
            <label><span>Forma y concentración <abbr title="Obligatorio">*</abbr></span><input required value={m.forma_concentracion} onChange={e => actualizar(i, 'forma_concentracion', e.target.value)} placeholder="Ej.: Cápsula 500 mg" /></label>
            <label className="med-field-wide"><span>Indicaciones (dosis, frecuencia, duración y vía) <abbr title="Obligatorio">*</abbr></span><textarea required rows={2} value={m.indicaciones} onChange={e => actualizar(i, 'indicaciones', e.target.value)} placeholder="Ej.: 1 cápsula cada 8 horas por 10 días, vía oral" /></label>
            <label>Cantidad recetada<input value={m.cantidad_recetada} onChange={e => actualizar(i, 'cantidad_recetada', e.target.value)} placeholder="Ej.: 30 cápsulas" /></label>
          </div>
        </fieldset>)}
        <button type="button" className="med-add-button" onClick={() => setMedicamentos(actual => [...actual, medicamentoVacio()])}>+ Añadir otro medicamento</button>
      </div>
      {mutation.isError && <p role="alert" className="med-error">No se pudo emitir la receta. Revisa los datos e inténtalo de nuevo.</p>}
      <div className="med-form-actions">
        <button className="primary-button" disabled={mutation.isPending}>Revisar y emitir…</button>
      </div>
    </form>
    <div className="med-panel-header"><h2>Recetas emitidas para este paciente</h2></div>
    {recetas.isPending && <p role="status" className="med-message">Cargando recetas…</p>}
    {recetas.isError && <p role="alert" className="med-error">No se pudieron cargar las recetas emitidas.</p>}
    {recetas.data?.length === 0 && <p className="med-message">Todavía no hay recetas emitidas.</p>}
    {recetas.data?.map(receta => <RecetaFicha key={receta.id} receta={receta} estado="Emitida a farmacia" />)}

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
