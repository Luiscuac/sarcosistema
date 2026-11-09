import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { guardarRecetaEnfermeria, obtenerRecetasEnfermeria, publicarRecetaEnfermeria } from '../api/enfermeriaApi.js'

const nuevoMedicamento = () => ({ nombre_generico: '', forma_concentracion: '', indicaciones: '', cantidad_recetada: '', cantidad_dispensada: '', valor_unitario: '', valor_total: '' })
const prestacionesDisponibles = ['Consulta integral', 'Control prenatal', 'Patología aguda', 'Desparasitación', 'Prevención de anemia', 'Anticoncepción', 'Curación de heridas', 'Inyectables', 'Vacunación', 'Urgencias', 'Otro']
const inicial = (paciente) => ({ establecimiento: '', programas: '', numero_receta: '', venta: false, historia_clinica: paciente.historia_clinica || '', tipo_atencion: 'consultorio', fecha: new Date().toISOString().slice(0, 10), diagnostico_principal: '', diagnostico_secundario: '', prestaciones: [], medicamentos: [nuevoMedicamento()], dispensador: '', prescriptor: '', costo_total: '', paciente_firma: '' })
const label = { nombre_generico: 'Nombre genérico', forma_concentracion: 'Forma farmacéutica y concentración', indicaciones: 'Indicaciones (cantidad, frecuencia, duración y vía)', cantidad_recetada: 'Cantidad recetada', cantidad_dispensada: 'Cantidad dispensada', valor_unitario: 'Valor unitario', valor_total: 'Valor total' }

export default function RecetaForm({ paciente }) {
  const cache = useQueryClient()
  const [form, setForm] = useState(() => inicial(paciente))
  const [ocupado, setOcupado] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const recetas = useQuery({ queryKey: ['enfermeria', 'recetas', paciente.id], queryFn: () => obtenerRecetasEnfermeria(paciente.id) })
  const cambiar = (campo, valor) => setForm(actual => ({ ...actual, [campo]: valor }))
  async function guardar(event) {
    event.preventDefault(); setOcupado(true); setError(''); setMensaje('')
    const datos = { ...form, prestaciones: form.prestaciones, medicamentos: form.medicamentos.map(m => ({ ...m, cantidad_recetada: m.cantidad_recetada || null, cantidad_dispensada: m.cantidad_dispensada || null, valor_unitario: m.valor_unitario === '' ? null : Number(m.valor_unitario), valor_total: m.valor_total === '' ? null : Number(m.valor_total) })), costo_total: form.costo_total === '' ? null : Number(form.costo_total) }
    try { await guardarRecetaEnfermeria(paciente.id, datos); await cache.invalidateQueries({ queryKey: ['enfermeria', 'recetas', paciente.id] }); setForm(inicial(paciente)); setMensaje('Borrador de receta guardado en la base de datos.') }
    catch (e) { const d=e.response?.data?.detail; setError(typeof d === 'string' ? d : 'No se pudo guardar la receta.') }
    finally { setOcupado(false) }
  }
  async function publicar(id) {
    if (!window.confirm('¿Publicar esta receta? El médico podrá verla en la ficha del paciente.')) return
    setOcupado(true); setError('')
    try { await publicarRecetaEnfermeria(id); await cache.invalidateQueries({ queryKey: ['enfermeria', 'recetas', paciente.id] }); setMensaje('Receta publicada para el médico.') }
    catch { setError('No se pudo publicar la receta.') } finally { setOcupado(false) }
  }
  return <section className="enf-panel">
    <div className="enf-panel-heading"><h2>Nueva receta de enfermería</h2><span>Guarda un borrador y publícalo para el médico.</span></div>
    <form className="enf-form" onSubmit={guardar}>
      <fieldset><legend>Datos de la receta</legend><div className="enf-measurements">
        <label>Establecimiento<input value={form.establecimiento} onChange={e=>cambiar('establecimiento',e.target.value)} /></label>
        <label>Programas<input value={form.programas} onChange={e=>cambiar('programas',e.target.value)} placeholder="Programas de salud" /></label>
        <label>Número de receta<input value={form.numero_receta} onChange={e=>cambiar('numero_receta',e.target.value)} /></label>
        <label>Historia clínica<input value={form.historia_clinica} onChange={e=>cambiar('historia_clinica',e.target.value)} /></label>
        <label>Tipo de atención<select value={form.tipo_atencion} onChange={e=>cambiar('tipo_atencion',e.target.value)}><option value="consultorio">En consultorio</option><option value="domiciliaria">Domiciliaria</option><option value="referencia">Referencia</option></select></label>
        <label>Fecha<input required type="date" value={form.fecha} onChange={e=>cambiar('fecha',e.target.value)} /></label>
        <label className="enf-check"><input type="checkbox" checked={form.venta} onChange={e=>cambiar('venta',e.target.checked)} /> Venta</label>
      </div></fieldset>
      <div className="enf-measurements"><label>Diagnóstico principal (CIE-10)<input value={form.diagnostico_principal} onChange={e=>cambiar('diagnostico_principal',e.target.value)} /></label><label>Diagnóstico secundario (CIE-10)<input value={form.diagnostico_secundario} onChange={e=>cambiar('diagnostico_secundario',e.target.value)} /></label></div>
      <fieldset><legend>Prestaciones realizadas</legend><div className="enf-checks">{prestacionesDisponibles.map(item=><label key={item}><input type="checkbox" checked={form.prestaciones.includes(item)} onChange={e=>cambiar('prestaciones',e.target.checked ? [...form.prestaciones,item] : form.prestaciones.filter(x=>x!==item))} />{item}</label>)}</div></fieldset>
      <fieldset><legend>Medicamentos e indicaciones</legend>{form.medicamentos.map((med,index)=><div className="enf-med-row" key={index}><strong>Medicamento {index+1}</strong><div className="enf-measurements">{Object.keys(label).map(campo=><label key={campo}>{label[campo]}{campo==='indicaciones' ? <textarea rows="2" required value={med[campo]} onChange={e=>cambiar('medicamentos',form.medicamentos.map((m,i)=>i===index?{...m,[campo]:e.target.value}:m))} /> : <input required={['nombre_generico','forma_concentracion'].includes(campo)} type={campo.startsWith('valor_')?'number':'text'} min={campo.startsWith('valor_')?'0':undefined} step={campo.startsWith('valor_')?'0.01':undefined} value={med[campo]} onChange={e=>cambiar('medicamentos',form.medicamentos.map((m,i)=>i===index?{...m,[campo]:e.target.value}:m))} />}</label>)}</div>{form.medicamentos.length>1&&<button type="button" onClick={()=>cambiar('medicamentos',form.medicamentos.filter((_,i)=>i!==index))}>Quitar medicamento</button>}</div>)}<button type="button" onClick={()=>cambiar('medicamentos',[...form.medicamentos,nuevoMedicamento()])}>Añadir medicamento</button></fieldset>
      <div className="enf-measurements"><label>Prescriptor / sello y firma<input value={form.prescriptor} onChange={e=>cambiar('prescriptor',e.target.value)} /></label><label>Dispensador<input value={form.dispensador} onChange={e=>cambiar('dispensador',e.target.value)} /></label><label>Costo total al usuario<input type="number" min="0" step="0.01" value={form.costo_total} onChange={e=>cambiar('costo_total',e.target.value)} /></label><label>Firma / C.I. paciente o acompañante<input value={form.paciente_firma} onChange={e=>cambiar('paciente_firma',e.target.value)} /></label></div>
      {error&&<p role="alert" className="enf-error">{error}</p>}{mensaje&&<p role="status" className="enf-message">{mensaje}</p>}<div className="enf-actions"><button className="primary-button" disabled={ocupado}>{ocupado?'Guardando…':'Guardar receta como borrador'}</button></div>
    </form>
    <div className="enf-panel-heading"><h2>Recetas registradas</h2></div>{recetas.data?.length===0&&<p className="enf-message">Aún no hay recetas.</p>}{recetas.data?.map(r=><article className="enf-record" key={r.id}><header><div><strong>Receta {r.numero_receta||`#${r.id}`} · {r.estado}</strong><span>{new Date(r.fecha).toLocaleDateString('es-BO')}</span></div>{r.estado==='borrador'&&<button type="button" className="primary-button" disabled={ocupado} onClick={()=>publicar(r.id)}>Publicar para el médico</button>}</header><p>{r.diagnostico_principal||'Sin diagnóstico'} · {r.medicamentos.map(m=>m.nombre_generico).join(', ')}</p></article>)}
  </section>
}
