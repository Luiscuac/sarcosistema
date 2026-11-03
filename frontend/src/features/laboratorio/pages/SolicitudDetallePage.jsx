import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { obtenerSolicitud } from '../api/laboratorioApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import RecibirMuestra from '../components/RecibirMuestra.jsx'
import { agruparPorCategoria, estadoSolicitud } from '../utils/agruparSolicitudes.js'
import './laboratorio.css'
import '../components/solicitudes/solicitudes-panel.css'
import './solicitud-detalle.css'

const etiquetaEstado = {
  pendiente_muestra: 'Pendiente de muestra',
  resultado_en_preparacion: 'En preparación',
  publicado: 'Publicado',
  no_realizado: 'No realizado',
}

function fechaVisible(valor) {
  return valor ? new Date(valor).toLocaleDateString('es-BO') : 'No registrada'
}

export default function SolicitudDetallePage({ usuario, logout }) {
  const { solicitudId } = useParams()
  const queryClient = useQueryClient()
  const [muestraAbierta, setMuestraAbierta] = useState(false)
  const { data: solicitud, isLoading, isError, error } = useQuery({
    queryKey: ['laboratorio', 'solicitud', solicitudId],
    queryFn: () => obtenerSolicitud(solicitudId),
  })
  const pendientes = solicitud?.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra') ?? []
  const informeDisponible = solicitud?.estudios.length > 0 && solicitud.estudios.every((estudio) => ['publicado', 'no_realizado'].includes(estudio.estado))
  const actualizar = () => queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud', solicitudId] })

  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-detail-page">
        <Link className="lab-back-link" to="/laboratorio">← Volver a solicitudes</Link>
        {isLoading && <p>Cargando solicitud…</p>}
        {isError && <div role="alert" className="lab-detail-card">
          <h1>{error?.response?.status === 404 ? 'Solicitud no encontrada' : 'No se pudo cargar la solicitud'}</h1>
          <p>Comprueba la referencia o intenta de nuevo desde la bandeja.</p>
        </div>}
        {solicitud && <>
          <div className="lab-title-row">
            <div><p className="lab-eyebrow">SOLICITUD DE LABORATORIO</p><h1>{solicitud.referencia}</h1>
              <p className="lab-intro">{solicitud.paciente_nombre} · {estadoSolicitud(solicitud.estudios)}</p></div>
            <span className="lab-view-label">{solicitud.prioridad === 'urgente' ? 'Urgente' : 'Programada'}</span>
          </div>
          <section className="lab-detail-card">
            <h2>Datos del pedido</h2>
            <dl className="lab-detail-grid">
              <div><dt>Paciente</dt><dd>{solicitud.paciente_nombre}</dd></div>
              <div><dt>Documento</dt><dd>{solicitud.paciente_documento || 'Sin documento'}</dd></div>
              <div><dt>Fecha de solicitud</dt><dd>{fechaVisible(solicitud.fecha_solicitud)}</dd></div>
              <div><dt>N.º de formulario D-8</dt><dd>{solicitud.referencia_papel_formulario || 'No registrado'}</dd></div>
              <div><dt>Procedencia</dt><dd>{solicitud.procedencia === 'otro_centro' ? solicitud.establecimiento_solicitante_nombre : 'Sarcobamba'}</dd></div>
              <div><dt>Profesional solicitante</dt><dd>{solicitud.medico_solicitante_nombre || 'No registrado'}</dd></div>
              <div><dt>Diagnóstico</dt><dd>{solicitud.diagnostico_principal || 'No registrado'}</dd></div>
              <div><dt>Registrada en el sistema</dt><dd>{solicitud.fecha_registro ? new Date(solicitud.fecha_registro).toLocaleString('es-BO') : 'No registrado'}</dd></div>
            </dl>
          </section>
          <section className="lab-detail-card lab-report-access">
            <div><h2>Informe final</h2><p>{informeDisponible ? 'La solicitud está finalizada. El informe reúne los resultados y los estudios no realizados.' : 'Disponible cuando cada estudio esté publicado o cerrado como no realizado.'}</p></div>
            {informeDisponible && <Link className="primary-button lab-report-link" to={`/laboratorio/solicitudes/${solicitud.id}/informe`}>Ver informe final</Link>}
          </section>
          {solicitud.muestras?.length > 0 && <section className="lab-detail-card">
            <h2>Muestras registradas</h2>
            {solicitud.muestras.map((muestra) => <p key={muestra.referencia}>
              <strong>{muestra.tipo_muestra}</strong> · {fechaVisible(muestra.fecha_toma)} · Recibió o tomó: {muestra.responsable_recepcion || 'No registrado'} · {muestra.estudio_ids.length} estudios
            </p>)}
          </section>}
          <section className="lab-detail-card">
            <div className="lab-detail-heading"><div><h2>Estudios solicitados</h2><p>{solicitud.estudios.length} estudios en este pedido</p></div>
              {pendientes.length > 0 && <button className="primary-button" type="button" onClick={() => setMuestraAbierta(true)}>Registrar muestra</button>}
            </div>
            {pendientes.length > 0 && <p className="lab-form-hint">Una misma muestra puede servir para varios estudios. Selecciónalos juntos al registrar la muestra; usa otro registro para orina, heces u otra toma. Si no se recibió, registra la incidencia desde ese mismo formulario.</p>}
            {agruparPorCategoria(solicitud.estudios).map((categoria) => <div className="lab-detail-group" key={categoria.codigo ?? 'otros'}>
              <div className="lab-detail-group-heading"><h3>{categoria.nombre}</h3>
                {categoria.codigo && categoria.estudios.some((estudio) => ['resultado_en_preparacion', 'publicado'].includes(estudio.estado)) && <Link className="lab-study-link" to={`/laboratorio/solicitudes/${solicitud.id}/areas/${categoria.codigo}/resultados`}>
                  {categoria.estudios.every((estudio) => ['publicado', 'no_realizado'].includes(estudio.estado))
                    ? 'Ver resultados del área'
                    : 'Capturar resultados'}
                </Link>}
              </div>
              {categoria.estudios.map((estudio) => <div className="lab-request-study" key={estudio.estudio_id}>
                <div><strong>{estudio.tipo_estudio_nombre}</strong><span>{etiquetaEstado[estudio.estado] || estudio.estado}</span>
                  {estudio.incidencias?.map((incidencia, index) => <span key={index} className="lab-incidence-note">
                    {incidencia.motivo === 'muestra_no_entregada' ? 'Muestra no entregada' : incidencia.motivo === 'toma_rechazada' ? 'Toma rechazada' : 'Toma no realizada'} · {incidencia.descripcion} · {incidencia.responsable} · {new Date(incidencia.fecha_hora).toLocaleString('es-BO')}
                  </span>)}
                </div>
              </div>)}
            </div>)}
          </section>
        </>}
      </section>
    </div>
    {muestraAbierta && solicitud && <RecibirMuestra solicitud={solicitud} onClose={() => setMuestraAbierta(false)} onReceived={() => { setMuestraAbierta(false); actualizar() }} />}
  </main>
}
