import { useQuery } from '@tanstack/react-query'
import { obtenerRecetasRecibidasEnfermeria } from '../api/enfermeriaApi.js'

export default function RecetasRecibidas({ pacienteId }) {
  const query = useQuery({ queryKey: ['enfermeria', 'recetas-recibidas', pacienteId],
    queryFn: () => obtenerRecetasRecibidasEnfermeria(pacienteId), enabled: Boolean(pacienteId) })
  return <section className="enf-panel">
    <div className="enf-panel-heading"><h2>Recetas emitidas por el médico</h2><span>Solo lectura</span></div>
    {query.isPending && <p role="status" className="enf-message">Cargando recetas…</p>}
    {query.isError && <p role="alert" className="enf-error">No se pudieron cargar las recetas.</p>}
    {query.data?.length === 0 && <p className="enf-message">Este paciente no tiene recetas emitidas.</p>}
    {query.data?.map(r => <article className="enf-record" key={r.id}>
      <header><div><strong>Receta {r.numero_receta || `#${r.id}`}</strong><span>{new Date(r.fecha).toLocaleDateString('es-BO')} · Médico: {r.registrado_por}</span></div></header>
      <p><strong>Diagnóstico:</strong> {r.diagnostico_principal || 'No indicado'}</p>
      <ul>{r.medicamentos.map((m, i) => <li key={`${r.id}-${i}`}><strong>{m.nombre_generico}</strong> · {m.forma_concentracion}<br />{m.indicaciones}<br />Cantidad: {m.cantidad_recetada || 'No especificada'}</li>)}</ul>
    </article>)}
  </section>
}
