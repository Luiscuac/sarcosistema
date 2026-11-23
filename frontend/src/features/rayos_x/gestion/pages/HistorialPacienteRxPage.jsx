import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { listarEstudiosPaciente, mensajeErrorApi } from '../../compartido/api/radiologiaApi.js'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import '../gestion.css'

const LATERALIDAD = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }
const fecha = (dato) => dato && !Number.isNaN(new Date(dato).getTime()) ? new Date(dato).toLocaleString('es-BO', { dateStyle: 'long', timeStyle: 'short' }) : 'Fecha no registrada'

export default function HistorialPacienteRxPage({ usuario, logout }) {
  const { pacienteId } = useParams()
  const consulta = useQuery({ queryKey: ['radiologia', 'paciente', pacienteId, 'estudios'], queryFn: ({ signal }) => listarEstudiosPaciente(pacienteId, signal) })
  const datos = consulta.data
  const estudios = [...(datos?.estudios ?? [])].sort((a, b) => new Date(b.fecha_solicitud).getTime() - new Date(a.fecha_solicitud).getTime())
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={{ volverA: '/rayos-x/gestion', textoVolver: 'Volver a estudios', migas: [{ texto: 'Estudios', ruta: '/rayos-x/gestion' }, { texto: datos?.paciente?.nombre_completo ?? 'Historial del paciente' }] }}>
    {consulta.isLoading && <div className="rxg-estado"><strong>Cargando historial...</strong></div>}
    {consulta.isError && <div className="rxg-estado" role="alert"><h1>{consulta.error?.response?.status === 404 ? 'Paciente no encontrado' : 'No se pudo cargar el historial'}</h1><span>{mensajeErrorApi(consulta.error, 'Vuelve a la bandeja e intenta nuevamente.')}</span></div>}
    {datos && <><div className="lab-title-row"><div><p className="lab-eyebrow">HISTORIAL DE RAYOS X</p><h1>{datos.paciente.nombre_completo}</h1><p className="lab-intro">{datos.paciente.numero_documento ? `Documento ${datos.paciente.numero_documento}` : 'Sin documento'} · {estudios.length} {estudios.length === 1 ? 'estudio' : 'estudios'}</p></div></div>
      <section className="lab-detail-card rxg-detalle-card rxg-historial"><h2>Estudios del paciente</h2>
        {estudios.length === 0 ? <div className="rxg-estado"><strong>No hay estudios de Rayos X registrados.</strong><span>Cuando se registre una solicitud aparecerá en este historial.</span></div> : <ol>{estudios.map((estudio) => <li key={estudio.estudio_id}><time dateTime={estudio.fecha_solicitud}>{fecha(estudio.fecha_solicitud)}</time><div><strong>{estudio.tipo_estudio_nombre}</strong><span>{LATERALIDAD[estudio.lateralidad] ?? 'Sin lateralidad'} · Solicitud <Link to={`/rayos-x/gestion/solicitudes/${estudio.solicitud_id}`}>{estudio.referencia_solicitud}</Link></span></div><span className={`rxg-etapa rxg-etapa--${estudio.etapa}`}>{estudio.etapa_texto}</span><Link className="lab-secondary-button" to={`/rayos-x/gestion/estudios/${estudio.estudio_id}`}>Abrir estudio</Link></li>)}</ol>}
      </section></>}
  </RayosXLayout>
}
