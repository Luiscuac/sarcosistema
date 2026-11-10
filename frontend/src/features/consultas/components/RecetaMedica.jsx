import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { emitirRecetaMedica } from '../api/consultasApi.js'
import { obtenerRecetasPublicadas } from '../../enfermeria/api/enfermeriaApi.js'

const medicamentoVacio = () => ({ nombre_generico: '', forma_concentracion: '', indicaciones: '', cantidad_recetada: '' })

export default function RecetaMedica({ paciente }) {
  const cache = useQueryClient()
  const [diagnostico, setDiagnostico] = useState('')
  const [medicamentos, setMedicamentos] = useState([medicamentoVacio()])
  const recetas = useQuery({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id],
    queryFn: () => obtenerRecetasPublicadas(paciente.id) })
  const mutation = useMutation({ mutationFn: datos => emitirRecetaMedica(paciente.id, datos),
    onSuccess: async () => {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'recetas-publicadas', paciente.id] })
      setDiagnostico(''); setMedicamentos([medicamentoVacio()])
    } })
  const actualizar = (i, campo, valor) => setMedicamentos(actual => actual.map((m, n) => n === i ? { ...m, [campo]: valor } : m))
  function enviar(evento) {
    evento.preventDefault()
    mutation.mutate({ fecha: new Date().toISOString().slice(0, 10), diagnostico_principal: diagnostico,
      medicamentos: medicamentos.map(m => ({ ...m, cantidad_dispensada: null, valor_unitario: null, valor_total: null })) })
  }
  return <section className="med-panel">
    <div className="med-panel-header"><h2>Receta médica</h2><span>Al emitirla, farmacia recibe el informe.</span></div>
    <form className="med-form" onSubmit={enviar}>
      <label>Diagnóstico<input required maxLength={1000} value={diagnostico} onChange={e => setDiagnostico(e.target.value)} /></label>
      {medicamentos.map((m, i) => <fieldset key={i}><legend>Medicamento {i + 1}</legend><div className="med-fields">
        <label>Nombre genérico<input required value={m.nombre_generico} onChange={e => actualizar(i, 'nombre_generico', e.target.value)} /></label>
        <label>Forma y concentración<input required value={m.forma_concentracion} onChange={e => actualizar(i, 'forma_concentracion', e.target.value)} /></label>
        <label>Indicaciones (dosis, frecuencia, duración y vía)<textarea required rows={3} value={m.indicaciones} onChange={e => actualizar(i, 'indicaciones', e.target.value)} /></label>
        <label>Cantidad recetada<input value={m.cantidad_recetada} onChange={e => actualizar(i, 'cantidad_recetada', e.target.value)} /></label>
      </div>{medicamentos.length > 1 && <button type="button" onClick={() => setMedicamentos(actual => actual.filter((_, n) => n !== i))}>Quitar</button>}</fieldset>)}
      <div className="med-form-actions"><button type="button" onClick={() => setMedicamentos(actual => [...actual, medicamentoVacio()])}>Añadir medicamento</button>
        <button className="primary-button" disabled={mutation.isPending}>{mutation.isPending ? 'Enviando…' : 'Emitir receta y enviar a farmacia'}</button></div>
      {mutation.isSuccess && <p role="status" className="med-message">Receta emitida y enviada a farmacia.</p>}
      {mutation.isError && <p role="alert" className="med-error">No se pudo emitir la receta.</p>}
    </form>
    <div className="med-panel-header"><h2>Recetas emitidas para este paciente</h2></div>
    {recetas.isPending && <p role="status" className="med-message">Cargando recetas…</p>}
    {recetas.isError && <p role="alert" className="med-error">No se pudieron cargar las recetas emitidas.</p>}
    {recetas.data?.length === 0 && <p className="med-message">Todavía no hay recetas emitidas.</p>}
    {recetas.data?.map(r => <article className="med-nursing-record" key={r.id}>
      <header><strong>Receta {r.numero_receta || `#${r.id}`} · emitida por {r.registrado_por}</strong><span>{new Date(r.fecha).toLocaleDateString('es-BO')} · {new Date(r.publicado_en).toLocaleString('es-BO')}</span></header>
      <p><strong>Diagnóstico:</strong> {r.diagnostico_principal || 'No indicado'}</p>
      <ul>{r.medicamentos.map((m, i) => <li key={`${r.id}-${i}`}><strong>{m.nombre_generico}</strong> · {m.forma_concentracion}<br />{m.indicaciones}<br />Cantidad: {m.cantidad_recetada || 'No especificada'}</li>)}</ul>
    </article>)}
  </section>
}
