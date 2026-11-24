import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { obtenerRegistrosPublicados } from '../api/enfermeriaApi.js'
import { usePaciente } from '../../consultas/hooks/useConsultas.js'
import { formatearFechaHora } from '../../../shared/utils/formatearFecha.js'

const campos = [
  ['motivo_consulta', 'Motivo referido'], ['sintomas', 'Síntomas referidos'],
  ['observaciones_enfermeria', 'Observaciones de enfermería'], ['peso_kg', 'Peso (kg)'],
  ['talla_cm', 'Talla (cm)'], ['temperatura_c', 'Temperatura (°C)'],
  ['frecuencia_cardiaca', 'Frecuencia cardíaca'], ['frecuencia_respiratoria', 'Frecuencia respiratoria'],
  ['presion_sistolica', 'Presión sistólica'], ['presion_diastolica', 'Presión diastólica'],
  ['saturacion_oxigeno', 'Saturación de oxígeno (%)'], ['dolor_escala', 'Dolor (0 a 10)'],
]
const fechaHora = (value) => value ? formatearFechaHora(value) : 'Sin fecha'

function CamposInforme({ registro, lista, titulo }) {
  const visibles = lista.filter(([campo]) => registro[campo] != null && registro[campo] !== '')
  if (!visibles.length) return null
  return <section className="med-report-section">
    <h3>{titulo}</h3>
    <dl className="med-report-fields">{visibles.map(([campo, etiqueta]) =>
      <div key={campo}><dt>{etiqueta}</dt><dd>{registro[campo]}</dd></div>)}</dl>
  </section>
}

export default function RegistrosPublicados({ pacienteId, registroId }) {
  const query = useQuery({
    queryKey: ['enfermeria', 'publicados', pacienteId],
    queryFn: () => obtenerRegistrosPublicados(pacienteId),
    enabled: Boolean(pacienteId),
  })
  const paciente = usePaciente(pacienteId)
  const detalle = Boolean(registroId)
  const registroSeleccionado = query.data?.find(registro => String(registro.id) === String(registroId))
  return <section className="med-panel med-nursing-panel">
    {!detalle && <div className="med-panel-header"><h2>Admisión y valoración de enfermería</h2><span>Registros publicados</span></div>}
    {query.isPending && <p role="status" className="med-message">Cargando registros de enfermería…</p>}
    {query.isError && <p role="alert" className="med-message">No se pudieron cargar los registros de enfermería.</p>}
    {!detalle && query.data?.length === 0 && <p className="med-message">No hay registros publicados para este paciente.</p>}
    {detalle && !registroSeleccionado && !query.isPending && !query.isError
      ? <p role="alert" className="med-message">No se pudo encontrar el informe de esta admisión.</p>
      : registroSeleccionado
      ? <>
        <header className="med-history-report-header">
          <div>
            <p className="med-eyebrow">INFORME DE ENFERMERÍA</p>
            <h2>Admisión y valoración</h2>
            <p>Publicado el {fechaHora(registroSeleccionado.publicado_en)}</p>
          </div>
          <Link className="med-prescription-back" to={`/consultas/pacientes/${pacienteId}?seccion=enfermeria`}>Volver a registros</Link>
        </header>
        <div className="med-history-report">
          <dl className="med-report-meta">
            <div><dt>Paciente</dt><dd>{paciente.data?.nombre_completo || 'Cargando paciente…'}</dd></div>
            <div><dt>Publicado por</dt><dd>{registroSeleccionado.publicado_por || registroSeleccionado.registrado_por || 'No indicado'}</dd></div>
            <div><dt>Fecha de publicación</dt><dd>{fechaHora(registroSeleccionado.publicado_en)}</dd></div>
          </dl>
          <CamposInforme registro={registroSeleccionado} lista={campos.slice(0, 3)} titulo="Motivo y valoración" />
          <CamposInforme registro={registroSeleccionado} lista={campos.slice(3)} titulo="Signos vitales" />
        </div>
      </>
      : !detalle && query.data?.map(registro => <article className="med-history-list-item" key={registro.id}>
        <div className="med-history-list-main">
          <strong>Admisión de enfermería</strong>
          <span>{fechaHora(registro.publicado_en)} · {registro.publicado_por || registro.registrado_por || 'Personal no indicado'}</span>
        </div>
        <p><span>Motivo referido</span>{registro.motivo_consulta || registro.sintomas || 'Valoración registrada'}</p>
        <Link className="med-history-open" to={`/consultas/pacientes/${pacienteId}/enfermeria/${registro.id}`}>Ver informe <span aria-hidden="true">→</span></Link>
      </article>)}
  </section>
}
