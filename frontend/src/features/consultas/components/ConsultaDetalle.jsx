import { Link } from 'react-router-dom'
import { useConsulta } from '../hooks/useConsultas.js'
import { fecha, IdentidadPaciente } from './PacienteFicha.jsx'
import { calcularImc, grupos } from '../utils/formulario.js'

function DetalleContenido({ consulta }) {
  const imc = calcularImc(consulta.peso_kg ?? '', consulta.talla_cm ?? '')
  return <>
    <div className="med-metadata"><span>Atención: <strong>{new Date(consulta.fecha_hora_inicio).toLocaleString('es-BO')}</strong></span><span>Médico: <strong>{consulta.medico_nombre}</strong></span><span>Consulta N.º {consulta.id} · {consulta.estado}</span></div>
    <section className="med-panel med-detail">{grupos.map((grupo) => <div className="med-detail-section" key={grupo.titulo}><h2>{grupo.titulo}</h2><dl>{grupo.campos.map(([campo, etiqueta]) => <div key={campo}><dt>{etiqueta.replace(' *', '')}</dt><dd>{consulta[campo] ?? 'No registrado'}</dd></div>)}{grupo.numerico && <div><dt>IMC calculado</dt><dd>{imc ?? 'No registrado'}</dd></div>}</dl></div>)}</section>
  </>
}

export default function ConsultaDetalle({ id }) {
  const consulta = useConsulta(id)
  if (consulta.isPending) return <p role="status">Cargando consulta…</p>
  if (consulta.isError) return <p role="alert">No se pudo recuperar la consulta.</p>
  return <><div className="med-heading"><div><p className="med-eyebrow">HISTORIA CLÍNICA</p><h1>Detalle de consulta</h1><p>Registro histórico de solo lectura · {fecha(consulta.data.fecha_hora_inicio)}</p></div><Link className="med-link-button" to={`/consultas/pacientes/${consulta.data.paciente_id}`}>Volver al historial</Link></div>{consulta.data.paciente && <><IdentidadPaciente paciente={consulta.data.paciente} />{consulta.data.paciente.estado !== 'activo' && <p className="med-hint">El paciente ya no está activo; esta consulta histórica se conserva en modo lectura.</p>}</>}<DetalleContenido consulta={consulta.data} /></>
}
