import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { obtenerRecetasRecibidasEnfermeria } from '../api/enfermeriaApi.js'
import { formatearFecha, formatearFechaHora } from '../../../shared/utils/formatearFecha.js'

function fechaReceta(receta) {
  return receta.publicado_en ? formatearFechaHora(receta.publicado_en) : formatearFecha(receta.fecha)
}

function RecetaResumen({ receta, onAbrir }) {
  return <article className="enf-history-list-item">
    <div className="enf-history-list-main">
      <strong>{receta.numero_receta || `Receta #${receta.id}`}</strong>
      <span>{fechaReceta(receta)}</span>
    </div>
    <p><span>Diagnóstico</span>{receta.diagnostico_principal || 'No indicado'}</p>
    <button type="button" className="enf-history-open" onClick={() => onAbrir(receta)}>
      Ver informe <span aria-hidden="true">→</span>
    </button>
  </article>
}

export default function RecetasRecibidas({ pacienteId, paciente }) {
  const navigate = useNavigate()
  const query = useQuery({ queryKey: ['enfermeria', 'recetas-recibidas', pacienteId],
    queryFn: () => obtenerRecetasRecibidasEnfermeria(pacienteId), enabled: Boolean(pacienteId) })
  return <section className="enf-panel enf-received-prescriptions">
    <div className="enf-panel-heading"><h2>Recetas emitidas por el médico</h2><span>Solo lectura{query.data ? ` · ${query.data.length}` : ''}</span></div>
    {query.isPending && <p role="status" className="enf-message">Cargando recetas…</p>}
    {query.isError && <p role="alert" className="enf-error">No se pudieron cargar las recetas.</p>}
    {query.data?.length === 0 && <div className="enf-received-prescriptions-empty">
      <span aria-hidden="true">Rx</span><h3>Aún no hay recetas emitidas</h3><p>Las recetas del médico aparecerán aquí.</p>
    </div>}
    {query.data?.length > 0 && <div className="enf-history-list">
      {query.data.map(receta => <RecetaResumen key={receta.id} receta={receta}
        onAbrir={(item) => navigate(`/enfermeria/pacientes/${pacienteId}/recetas/${item.id}/informe`,
          { state: { paciente, receta: item, pantalla: 'recetas' } })} />)}
    </div>}
  </section>
}
