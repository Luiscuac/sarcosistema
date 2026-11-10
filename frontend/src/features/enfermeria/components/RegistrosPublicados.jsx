import { useQuery } from '@tanstack/react-query'
import { obtenerRegistrosPublicados } from '../api/enfermeriaApi.js'

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
  </section>
}
