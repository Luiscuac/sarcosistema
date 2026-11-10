import { useQuery } from '@tanstack/react-query'
import { obtenerRecetasRecibidasEnfermeria } from '../api/enfermeriaApi.js'
import RecetaFicha from './RecetaFicha.jsx'

export default function RecetasRecibidas({ pacienteId }) {
  const query = useQuery({ queryKey: ['enfermeria', 'recetas-recibidas', pacienteId],
    queryFn: () => obtenerRecetasRecibidasEnfermeria(pacienteId), enabled: Boolean(pacienteId) })
  return <section className="enf-panel">
    <div className="enf-panel-heading"><h2>Recetas emitidas por el médico</h2><span>Solo lectura</span></div>
    {query.isPending && <p role="status" className="enf-message">Cargando recetas…</p>}
    {query.isError && <p role="alert" className="enf-error">No se pudieron cargar las recetas.</p>}
    {query.data?.length === 0 && <p className="enf-message">Este paciente no tiene recetas emitidas.</p>}
    {query.data?.map(receta => <RecetaFicha key={receta.id} receta={receta} estado="Disponible para el equipo" />)}
  </section>
}
