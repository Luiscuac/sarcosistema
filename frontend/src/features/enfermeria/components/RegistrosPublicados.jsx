import { useQuery } from '@tanstack/react-query'
import { obtenerRecetasPublicadas, obtenerRegistrosPublicados } from '../api/enfermeriaApi.js'

const campos = [
  ['motivo_consulta', 'Motivo referido'], ['sintomas', 'Síntomas referidos'],
  ['observaciones_enfermeria', 'Observaciones de enfermería'], ['peso_kg', 'Peso (kg)'],
  ['talla_cm', 'Talla (cm)'], ['temperatura_c', 'Temperatura (°C)'],
  ['frecuencia_cardiaca', 'Frecuencia cardíaca'], ['frecuencia_respiratoria', 'Frecuencia respiratoria'],
  ['presion_sistolica', 'Presión sistólica'], ['presion_diastolica', 'Presión diastólica'],
  ['saturacion_oxigeno', 'Saturación de oxígeno (%)'], ['dolor_escala', 'Dolor (0 a 10)'],
]
const fechaHora = (value) => value ? new Date(value).toLocaleString('es-BO') : 'Sin fecha'

export default function RegistrosPublicados({ pacienteId }) {
  const query = useQuery({
    queryKey: ['enfermeria', 'publicados', pacienteId],
    queryFn: () => obtenerRegistrosPublicados(pacienteId),
    enabled: Boolean(pacienteId),
  })
  const recetas = useQuery({ queryKey: ['enfermeria', 'recetas-publicadas', pacienteId], queryFn: () => obtenerRecetasPublicadas(pacienteId), enabled: Boolean(pacienteId) })
  return <section className="med-panel med-nursing-panel">
    <div className="med-panel-header"><h2>Admisión y valoración de enfermería</h2><span>Registros publicados</span></div>
    {query.isPending && <p role="status" className="med-message">Cargando registros de enfermería…</p>}
    {query.isError && <p role="alert" className="med-message">No se pudieron cargar los registros de enfermería.</p>}
    {query.data?.length === 0 && <p className="med-message">No hay registros publicados para este paciente.</p>}
    {query.data?.map((registro) => <article className="med-nursing-record" key={registro.id}>
      <header><strong>Publicado por {registro.publicado_por || registro.registrado_por}</strong>
        <span>{fechaHora(registro.publicado_en)}</span></header>
      <dl>{campos.filter(([campo]) => registro[campo] != null && registro[campo] !== '').map(([campo, etiqueta]) =>
        <div key={campo}><dt>{etiqueta}</dt><dd>{registro[campo]}</dd></div>)}</dl>
    </article>)}
    <div className="med-panel-header"><h2>Recetas emitidas</h2><span>Enviadas a farmacia y visibles para enfermería</span></div>
    {recetas.isPending && <p role="status" className="med-message">Cargando recetas…</p>}
    {recetas.isError && <p role="alert" className="med-message">No se pudieron cargar las recetas.</p>}
    {recetas.data?.length === 0 && <p className="med-message">No hay recetas emitidas para este paciente.</p>}
    {recetas.data?.map(receta => <article className="med-nursing-record" key={receta.id}>
      <header><strong>Receta {receta.numero_receta || `#${receta.id}`} · emitida por {receta.registrado_por}</strong><span>{new Date(receta.fecha).toLocaleDateString('es-BO')} · enviada {fechaHora(receta.publicado_en)}</span></header>
      <dl>{[['establecimiento','Establecimiento'],['programas','Programas'],['historia_clinica','Historia clínica'],['tipo_atencion','Tipo de atención'],['diagnostico_principal','Diagnóstico principal (CIE-10)'],['diagnostico_secundario','Diagnóstico secundario (CIE-10)'],['prescriptor','Prescriptor / firma'],['dispensador','Dispensador'],['costo_total','Costo total'],['paciente_firma','Firma / C.I. paciente']].filter(([key])=>receta[key]).map(([key,title])=><div key={key}><dt>{title}</dt><dd>{receta[key]}</dd></div>)}</dl>
      {receta.prestaciones?.length>0&&<p><strong>Prestaciones:</strong> {receta.prestaciones.join(', ')}</p>}
      <h3>Medicamentos e indicaciones</h3><ul>{receta.medicamentos.map((m,i)=><li key={i}><strong>{m.nombre_generico}</strong> · {m.forma_concentracion}<br />{m.indicaciones}<br />Recetada: {m.cantidad_recetada||'—'} · Dispensada: {m.cantidad_dispensada||'—'} · Valor: {m.valor_total??'—'}</li>)}</ul>
    </article>)}
  </section>
}
