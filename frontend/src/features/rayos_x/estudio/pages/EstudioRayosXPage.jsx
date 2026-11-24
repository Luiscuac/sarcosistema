import { useState } from 'react'
import { Link, Navigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import ConfirmarAccion from '../../../../shared/ui/ConfirmarAccion.jsx'
import Boton, { BotonEnlace } from '../../../../shared/ui/Boton.jsx'
import { entregarEstudio, marcarNoRealizado } from '../../compartido/api/radiologiaApi.js'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'
import { formatearFechaHora } from '../../../../shared/utils/formatearFecha.js'
import RecorridoRx from '../components/RecorridoRx.jsx'
import { navegacionEstudio, useEstudioRx } from '../hooks/useEstudioRx.js'
import { accionPrincipalRx } from '../utils/flujo.js'
import '../../../laboratorio/pages/solicitud-detalle.css'
import './estudio.css'

const LATERALIDAD = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }
const nombresProyeccion = (codigos, config) => (codigos || []).map(c => config?.proyecciones?.find(p => p.codigo === c)?.nombre || c).join(', ')
const DESCRIPCION_ETAPA = {
  pendiente_realizacion: 'Aún no se registró la adquisición.',
  en_adquisicion: 'Adquisición en curso: falta completar el registro o las imágenes.',
  pendiente_informe: 'Imágenes listas. Falta redactar el informe.',
  borrador: 'Hay un borrador del informe. Continúa y valídalo cuando esté completo.',
  validado: 'Informe validado. Falta registrar la entrega.',
  entregado: 'Informe validado y entregado.',
  no_realizado: 'El estudio se cerró sin tomar imágenes. El motivo queda en el historial.',
  anulado: 'El estudio fue anulado.',
}
// Enlaces antiguos con ?seccion= (pestañas que ya no existen).
const SECCION_A_RUTA = { adquisicion: 'adquisicion', informe: 'informe' }

function DatosPedido({ detalle }) {
  const { paciente, solicitud, estudio, adquisicion, config } = detalle
  const solicitadas = nombresProyeccion(estudio.detalle?.proyecciones_solicitadas, config)
  const realizadas = nombresProyeccion(adquisicion?.proyecciones_realizadas, config)
  const filas = [
    ['Paciente', <Link key="p" to={`/rayos-x/gestion/pacientes/${paciente.id}`}>{paciente.nombre_completo}</Link>],
    ['Documento', paciente.numero_documento || 'No registrado'],
    ['Edad / sexo', `${paciente.edad ?? '—'} / ${paciente.sexo || '—'}`],
    ['Médico solicitante', solicitud.medico_solicitante || 'No registrado'],
    ['Indicación clínica', estudio.detalle?.indicacion_clinica || 'No registrada'],
    ['Prioridad', estudio.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'],
    ['Solicitud', <Link key="s" to={`/rayos-x/gestion/solicitudes/${solicitud.id}`}>{solicitud.referencia}</Link>],
    ['Región', config?.region || 'No registrada'],
    ['Proyecciones solicitadas', solicitadas || 'No indicadas'],
    ...(realizadas ? [['Proyecciones realizadas', realizadas]] : []),
    ...(estudio.detalle?.observaciones ? [['Observaciones', estudio.detalle.observaciones]] : []),
  ]
  return <section className="lab-detail-card"><h2>Datos del pedido</h2>
    <dl className="lab-detail-grid">{filas.map(([dt, dd]) => <div key={dt}><dt>{dt}</dt><dd>{dd}</dd></div>)}</dl>
  </section>
}

function Historial({ historial }) {
  return <section className="lab-detail-card"><h2>Historial</h2>
    <ol className="rxe-linea-tiempo">{historial?.length ? historial.map((item, i) => <li key={`${item.fecha_hora}-${i}`}>
      <time>{formatearFechaHora(item.fecha_hora)}</time><strong>{item.descripcion}</strong><span>{item.usuario || 'Sistema'}</span>
    </li>) : <li>No hay eventos registrados.</li>}</ol>
  </section>
}

/** Detalle del estudio: dónde está, qué sigue y los datos del pedido (mismo esquema que una solicitud de Laboratorio). */
export default function EstudioRayosXPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const [params] = useSearchParams()
  const { data: detalle, isLoading, isError, error, actualizar } = useEstudioRx(estudioId)
  const { notificar } = useNotificacion()
  const [accion, setAccion] = useState(null)
  const [valor, setValor] = useState('')
  const cerrar = () => { setAccion(null); setValor('') }
  const opciones = mensaje => ({ onSuccess: d => { actualizar(d); cerrar(); notificar(mensaje, 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const noRealizado = useMutation({ mutationFn: () => marcarNoRealizado(estudioId, valor.trim()), ...opciones('Estudio marcado como no realizado.') })
  const entregar = useMutation({ mutationFn: () => entregarEstudio(estudioId, valor.trim()), ...opciones('Entrega registrada.') })

  const seccion = SECCION_A_RUTA[params.get('seccion')]
  if (seccion) return <Navigate to={`/rayos-x/gestion/estudios/${estudioId}/${seccion}`} replace />

  const principal = detalle && accionPrincipalRx(detalle)
  const etapa = detalle?.estudio.etapa
  const lateralidad = LATERALIDAD[detalle?.estudio.detalle?.lateralidad]
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacionEstudio(detalle, estudioId)} clase="lab-detail-page">
    {isLoading && <p role="status">Cargando estudio…</p>}
    {isError && <div role="alert" className="lab-detail-card"><h1>No se pudo cargar el estudio</h1><p>{mensajeError(error)}</p></div>}
    {detalle && <>
      <div className="lab-title-row">
        <div>
          <p className="lab-eyebrow">ESTUDIO DE RAYOS X · {detalle.estudio.referencia_estudio}</p>
          <h1>{detalle.paciente.nombre_completo}</h1>
          <p className="lab-intro">{detalle.estudio.tipo_estudio_nombre}{lateralidad ? ` · ${lateralidad}` : ''} · {detalle.estudio.etapa_texto}
            {detalle.estudio.prioridad === 'urgente' && <> · <strong className="lab-priority">Urgente</strong></>}</p>
        </div>
        {principal && <div className="lab-title-actions">{principal.ruta
          ? <BotonEnlace to={principal.ruta}>{principal.etiqueta}</BotonEnlace>
          : <Boton onClick={() => setAccion(principal.accion)}>{principal.etiqueta}</Boton>}</div>}
      </div>

      <section className={`lab-detail-card${['no_realizado', 'anulado'].includes(etapa) ? ' rx-detalle-cerrado' : ''}`}>
        <div className="lab-detail-heading"><div><h2>Recorrido del estudio</h2><p>{DESCRIPCION_ETAPA[etapa]}</p></div><RecorridoRx etapa={etapa} /></div>
        {detalle.imagenes?.length > 0 && <p className="lab-form-hint">{detalle.imagenes.length} {detalle.imagenes.length === 1 ? 'imagen' : 'imágenes'} en el estudio.</p>}
      </section>

      {['validado', 'entregado'].includes(etapa) && principal?.ruta?.endsWith('/impresion') !== true && <section className="lab-detail-card lab-report-access">
        <div><h2>Informe final</h2><p>Documento validado, listo para imprimir o guardar en PDF.</p></div>
        <BotonEnlace variante="secundario" to={`/rayos-x/gestion/estudios/${estudioId}/impresion`}>Ver informe impreso</BotonEnlace>
      </section>}
      {['pendiente_informe', 'borrador'].includes(etapa) && !principal && <section className="lab-detail-card lab-report-access">
        <div><h2>Informe</h2><p>Puedes consultar el borrador y las imágenes en modo de lectura.</p></div>
        <BotonEnlace variante="secundario" to={`/rayos-x/gestion/estudios/${estudioId}/informe`}>Ver informe</BotonEnlace>
      </section>}

      <DatosPedido detalle={detalle} />

      {detalle.informes_externos?.length > 0 && <section className="lab-detail-card"><h2>Informes externos</h2><ul className="rxe-lista">{detalle.informes_externos.map(x => <li key={x.id}><div>
        <strong>{x.establecimiento}</strong><span>{x.profesional || 'Profesional no informado'} · {x.fecha_informe || formatearFechaHora(x.fecha_carga)}</span></div></li>)}</ul></section>}

      <Historial historial={detalle.historial} />

      {detalle.permisos.marcar_no_realizado && <p className="rxe-no-realizado"><button type="button" className="rxe-enlace-peligro" onClick={() => setAccion('no-realizado')}>Marcar este estudio como no realizado</button></p>}
      {accion && <ConfirmarAccion titulo={accion === 'entregar' ? 'Registrar entrega' : 'Marcar como no realizado'} textoConfirmar={accion === 'entregar' ? 'Registrar entrega' : 'Marcar como no realizado'}
        peligro={accion !== 'entregar'} pendiente={noRealizado.isPending || entregar.isPending} onCancelar={cerrar}
        onConfirmar={() => valor.trim() && (accion === 'entregar' ? entregar.mutate() : noRealizado.mutate())}>
        <label className="lab-search-label">{accion === 'entregar' ? 'Entregado a' : 'Motivo'} *<textarea required value={valor} onChange={e => setValor(e.target.value)} /></label>
        {!valor.trim() && <p className="lab-form-hint">Este dato es obligatorio.</p>}
      </ConfirmarAccion>}
    </>}
  </RayosXLayout>
}
