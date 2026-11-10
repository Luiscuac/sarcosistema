import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { obtenerSolicitud } from '../api/laboratorioApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NavegacionLab from '../components/NavegacionLab.jsx'
import RecibirMuestra from '../components/RecibirMuestra.jsx'
import RecorridoEstudio from '../components/solicitudes/RecorridoEstudio.jsx'
import ProgresoSolicitud from '../components/solicitudes/ProgresoSolicitud.jsx'
import { agruparPorCategoria, estadoSolicitud } from '../utils/agruparSolicitudes.js'
import { progresoSolicitud, siguienteAccion } from '../utils/bandeja.js'
import { ESTADOS_FINALES, nombreMotivoIncidencia, nombreSexo } from '../utils/catalogos.js'
import { describirEdad } from '../../../shared/utils/edad.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import './laboratorio.css'
import '../components/solicitudes/solicitudes-panel.css'
import './solicitud-detalle.css'

const fechaVisible = (valor) => (valor ? formatearFecha(valor) : 'No registrada')
const fechaHora = (valor) => (valor ? new Date(valor).toLocaleString('es-BO') : 'No registrado')

function AccionPrincipal({ solicitud, onRegistrarMuestra }) {
  const accion = siguienteAccion(solicitud)
  if (accion.tipo === 'muestra') {
    return <button className="primary-button" type="button" onClick={onRegistrarMuestra}>Registrar muestra</button>
  }
  if (accion.tipo === 'abrir') return null
  return <Link className="primary-button lab-report-link" to={accion.ruta}>{accion.etiqueta}</Link>
}

function DatosPedido({ solicitud }) {
  const edad = describirEdad(solicitud.paciente_fecha_nacimiento)
  return <section className="lab-detail-card">
    <h2>Datos del pedido</h2>
    <dl className="lab-detail-grid">
      <div><dt>Paciente</dt><dd>{solicitud.paciente_nombre}</dd></div>
      <div><dt>Documento</dt><dd>{solicitud.paciente_documento || 'Sin documento'}</dd></div>
      <div><dt>Edad y sexo</dt><dd>{[edad, solicitud.paciente_sexo && nombreSexo(solicitud.paciente_sexo)].filter(Boolean).join(' · ') || 'No registrado'}</dd></div>
      <div><dt>Fecha de solicitud</dt><dd>{fechaVisible(solicitud.fecha_solicitud)}</dd></div>
      <div><dt>Procedencia</dt><dd>{solicitud.procedencia === 'otro_centro' ? solicitud.establecimiento_solicitante_nombre : 'Sarcobamba'}</dd></div>
      <div><dt>Profesional solicitante</dt><dd>{solicitud.medico_solicitante_nombre || 'No registrado'}</dd></div>
      <div><dt>Diagnóstico</dt><dd>{solicitud.diagnostico_principal || 'No registrado'}</dd></div>
      <div><dt>N.º de formulario D-8</dt><dd>{solicitud.referencia_papel_formulario || 'No registrado'}</dd></div>
      <div><dt>Registrada en el sistema</dt><dd>{fechaHora(solicitud.fecha_registro)}</dd></div>
    </dl>
  </section>
}

function MuestrasRegistradas({ muestras }) {
  if (!muestras?.length) return null
  return <section className="lab-detail-card">
    <h2>Muestras registradas</h2>
    <div className="lab-table-wrap">
      <table className="lab-simple-table">
        <thead><tr><th>Tipo</th><th>Fecha de toma</th><th>Recibió o tomó</th><th>Estudios</th><th>Referencia</th></tr></thead>
        <tbody>{muestras.map((muestra) => <tr key={muestra.referencia}>
          <td><strong>{muestra.tipo_muestra}</strong></td>
          <td>{fechaVisible(muestra.fecha_toma)}</td>
          <td>{muestra.responsable_recepcion || 'No registrado'}</td>
          <td>{muestra.estudio_ids.length}</td>
          <td><small>{muestra.referencia}</small></td>
        </tr>)}</tbody>
      </table>
    </div>
  </section>
}

function EstudiosPorArea({ solicitud }) {
  return agruparPorCategoria(solicitud.estudios).map((categoria) => {
    const conResultados = categoria.estudios.some((estudio) => ['resultado_en_preparacion', 'publicado'].includes(estudio.estado))
    const areaCerrada = categoria.estudios.every((estudio) => ESTADOS_FINALES.has(estudio.estado))
    return <div className="lab-detail-group" key={categoria.codigo ?? 'otros'}>
      <div className="lab-detail-group-heading"><h3>{categoria.nombre}</h3>
        {categoria.codigo && conResultados && <Link className={areaCerrada ? 'lab-study-link' : 'lab-study-link is-primary'}
          to={`/laboratorio/solicitudes/${solicitud.id}/areas/${categoria.codigo}/resultados`}>
          {areaCerrada ? 'Ver resultados del área' : 'Capturar resultados'}
        </Link>}
      </div>
      {categoria.estudios.map((estudio) => <div className="lab-request-study" key={estudio.estudio_id}>
        <div>
          <strong>{estudio.tipo_estudio_nombre}</strong>
          {estudio.incidencias?.map((incidencia, indice) => <span key={indice} className="lab-incidence-note">
            {nombreMotivoIncidencia(incidencia.motivo)} · {incidencia.descripcion} · {incidencia.responsable} · {fechaHora(incidencia.fecha_hora)}
          </span>)}
        </div>
        <RecorridoEstudio estado={estudio.estado} />
      </div>)}
    </div>
  })
}

export default function SolicitudDetallePage({ usuario, logout }) {
  const { solicitudId } = useParams()
  const [parametros, setParametros] = useSearchParams()
  const queryClient = useQueryClient()
  const [muestraAbierta, setMuestraAbierta] = useState(false)
  const { data: solicitud, isLoading, isError, error } = useQuery({
    queryKey: ['laboratorio', 'solicitud', solicitudId],
    queryFn: () => obtenerSolicitud(solicitudId),
  })
  const pendientes = solicitud?.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra') ?? []
  // "?accion=muestra" llega desde la bandeja o tras crear la solicitud: abre el registro directamente.
  const abrirDesdeEnlace = parametros.get('accion') === 'muestra' && pendientes.length > 0
  const dialogoMuestra = muestraAbierta || abrirDesdeEnlace

  function cerrarMuestra() {
    setMuestraAbierta(false)
    if (parametros.has('accion')) setParametros({}, { replace: true })
  }

  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-detail-page">
        <NavegacionLab volverA="/laboratorio" textoVolver="Volver a solicitudes"
          migas={[{ texto: 'Solicitudes', ruta: '/laboratorio' }, { texto: solicitud?.referencia ?? 'Solicitud' }]} />
        {isLoading && <p>Cargando solicitud…</p>}
        {isError && <div role="alert" className="lab-detail-card">
          <h1>{error?.response?.status === 404 ? 'Solicitud no encontrada' : 'No se pudo cargar la solicitud'}</h1>
          <p>Comprueba la referencia o intenta de nuevo desde la bandeja.</p>
        </div>}
        {solicitud && <>
          <div className="lab-title-row">
            <div><p className="lab-eyebrow">SOLICITUD DE LABORATORIO · {solicitud.referencia}</p><h1>{solicitud.paciente_nombre}</h1>
              <p className="lab-intro">{estadoSolicitud(solicitud.estudios)} · {solicitud.prioridad === 'urgente' ? <strong className="lab-priority">Urgente</strong> : 'Programada'}</p></div>
            <div className="lab-title-actions">
              <ProgresoSolicitud estudios={solicitud.estudios} />
              <AccionPrincipal solicitud={solicitud} onRegistrarMuestra={() => setMuestraAbierta(true)} />
            </div>
          </div>
          <section className="lab-detail-card">
            <div className="lab-detail-heading"><div><h2>Estudios solicitados</h2><p>{solicitud.estudios.length} estudios en este pedido</p></div>
              {pendientes.length > 0 && <button type="button" className="lab-secondary-button" onClick={() => setMuestraAbierta(true)}>Registrar muestra o incidencia</button>}
            </div>
            {pendientes.length > 0 && <p className="lab-form-hint">Una misma muestra puede servir para varios estudios. Si no se recibió, registra la incidencia desde ese mismo formulario.</p>}
            <EstudiosPorArea solicitud={solicitud} />
          </section>
          {progresoSolicitud(solicitud.estudios).completa && <section className="lab-detail-card lab-report-access">
            <div><h2>Informe final</h2><p>La solicitud está finalizada. El informe reúne los resultados y los estudios no realizados.</p></div>
            <Link className="primary-button lab-report-link" to={`/laboratorio/solicitudes/${solicitud.id}/informe`}>Ver informe final</Link>
          </section>}
          <DatosPedido solicitud={solicitud} />
          <MuestrasRegistradas muestras={solicitud.muestras} />
        </>}
      </section>
    </div>
    {dialogoMuestra && solicitud && <RecibirMuestra solicitud={solicitud} usuario={usuario} onClose={cerrarMuestra}
      onReceived={() => { cerrarMuestra(); queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud', solicitudId] }) }} />}
  </main>
}
