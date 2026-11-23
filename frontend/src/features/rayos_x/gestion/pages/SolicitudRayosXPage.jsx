import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { obtenerSolicitud } from '../../compartido/api/radiologiaApi.js'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import '../gestion.css'
import { BotonEnlace } from '../../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'

const LATERALIDAD = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }
const valor = (dato) => dato || 'No registrado'
const fecha = (dato) => dato && !Number.isNaN(new Date(dato).getTime()) ? new Date(dato).toLocaleString('es-BO', { dateStyle: 'long', timeStyle: 'short' }) : 'No registrada'

export default function SolicitudRayosXPage({ usuario, logout }) {
  const { solicitudId } = useParams()
  const consulta = useQuery({ queryKey: ['radiologia', 'solicitud', solicitudId], queryFn: ({ signal }) => obtenerSolicitud(solicitudId, signal) })
  const datos = consulta.data
  const solicitud = datos?.solicitud
  const paciente = datos?.paciente
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={{ volverA: '/rayos-x/gestion', textoVolver: 'Volver a estudios', migas: [{ texto: 'Estudios', ruta: '/rayos-x/gestion' }, { texto: solicitud?.referencia ?? 'Solicitud' }] }}>
    {consulta.isLoading && <div className="rxg-estado"><strong>Cargando solicitud...</strong></div>}
    {consulta.isError && <div className="rxg-estado" role="alert"><h1>{consulta.error?.response?.status === 404 ? 'Solicitud no encontrada' : 'No se pudo cargar la solicitud'}</h1><span>{mensajeError(consulta.error, 'Vuelve a la bandeja e intenta nuevamente.')}</span></div>}
    {datos && <>
      <div className="lab-title-row"><div><p className="lab-eyebrow">SOLICITUD · {solicitud.referencia}</p><h1>{paciente.nombre_completo}</h1><p className="lab-intro">{solicitud.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'} · {datos.estudios.length} {datos.estudios.length === 1 ? 'estudio' : 'estudios'}</p></div></div>
      <section className="lab-detail-card rxg-detalle-card"><div className="rxg-detalle-heading"><div><h2>Paciente</h2><p>Datos de identificación asociados al pedido.</p></div><BotonEnlace variante="secundario" to={`/rayos-x/gestion/pacientes/${paciente.id}`}>Ver historial de Rayos X</BotonEnlace></div>
        <dl className="lab-detail-grid rxg-datos"><div><dt>Nombre</dt><dd>{paciente.nombre_completo}</dd></div><div><dt>Documento</dt><dd>{valor(paciente.numero_documento)}</dd></div><div><dt>Código de paciente</dt><dd>{valor(paciente.codigo_paciente)}</dd></div><div><dt>Fecha de nacimiento</dt><dd>{valor(paciente.fecha_nacimiento)}</dd></div><div><dt>Sexo</dt><dd>{valor(paciente.sexo)}</dd></div><div><dt>Edad</dt><dd>{paciente.edad ?? 'No registrada'}</dd></div></dl>
      </section>
      <section className="lab-detail-card rxg-detalle-card"><h2>Datos del pedido</h2><dl className="lab-detail-grid rxg-datos"><div><dt>Referencia</dt><dd>{solicitud.referencia}</dd></div><div><dt>Fecha</dt><dd>{fecha(solicitud.fecha_solicitud)}</dd></div><div><dt>Procedencia</dt><dd>{solicitud.procedencia === 'otro_centro' ? 'Otro centro' : 'Este centro'}</dd></div><div><dt>Médico solicitante</dt><dd>{valor(solicitud.medico_solicitante ?? solicitud.medico_solicitante_nombre)}</dd></div><div><dt>Establecimiento</dt><dd>{valor(solicitud.establecimiento ?? solicitud.establecimiento_solicitante_nombre)}</dd></div><div><dt>Diagnóstico o motivo</dt><dd>{valor(solicitud.diagnostico_principal)}</dd></div></dl></section>
      <section className="lab-detail-card rxg-detalle-card"><h2>Estudios solicitados</h2><div className="rxg-estudios-lista">{datos.estudios.map((estudio) => <div className="rxg-estudio-fila" key={estudio.estudio_id}><div className="rxg-estudio-identidad"><strong>{estudio.tipo_estudio_nombre}</strong><span>{LATERALIDAD[estudio.lateralidad] ?? 'Sin lateralidad'} · {estudio.referencia_estudio}</span></div><span className={`rxg-etapa rxg-etapa--${estudio.etapa}`}>{estudio.etapa_texto}</span><Link className="lab-secondary-button rxg-abrir" to={`/rayos-x/gestion/estudios/${estudio.estudio_id}`}>Abrir estudio</Link></div>)}</div></section>
    </>}
  </RayosXLayout>
}
