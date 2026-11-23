import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import ConfirmarAccion from '../../../../shared/ui/ConfirmarAccion.jsx'
import { entregarEstudio, marcarNoRealizado, obtenerEstudio } from '../../compartido/api/radiologiaApi.js'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import SeccionAdquisicion from '../components/SeccionAdquisicion.jsx'
import SeccionInforme from '../components/SeccionInforme.jsx'
import '../../asistente/pages/rayos-x.css'
import './estudio.css'
import Boton, { BotonEnlace } from '../../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'

const SECCIONES = ['resumen', 'adquisicion', 'informe', 'historial']
const NOMBRES_SECCION = { resumen: 'Resumen', adquisicion: 'Adquisición e imágenes', informe: 'Informe', historial: 'Historial' }
const lateralidad = valor => ({ derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }[valor] || 'No aplica')
const proyecciones = (codigos, config) => (codigos || []).map(c => config?.proyecciones?.find(p => p.codigo === c)?.nombre || c).join(', ') || 'Ninguna registrada'

const ETAPAS = ['solicitado', 'adquisicion', 'informe', 'entrega']
const ETAPAS_TEXTO = { solicitado: 'Solicitud', adquisicion: 'Adquisición', informe: 'Informe', entrega: 'Entrega' }
// Estado de cada paso del flujo según la etapa del estudio.
function avanceDelFlujo(etapa) {
  const actual = { pendiente_realizacion: 'adquisicion', en_adquisicion: 'adquisicion', pendiente_informe: 'informe', borrador: 'informe', validado: 'entrega', entregado: null }[etapa]
  const indice = actual ? ETAPAS.indexOf(actual) : ETAPAS.length
  return ETAPAS.map((id, i) => ({ id, estado: i < indice ? 'hecho' : i === indice ? 'actual' : 'pendiente' }))
}

function Resumen({ estudioId, detalle, irA }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion(); const [accion, setAccion] = useState(null); const [valor, setValor] = useState('')
  const clave = ['radiologia', 'estudio', estudioId]; const actualizar = d => queryClient.setQueryData(clave, d)
  const noRealizado = useMutation({ mutationFn: () => marcarNoRealizado(estudioId, valor.trim()), onSuccess: d => { actualizar(d); setAccion(null); setValor(''); notificar('Estudio marcado como no realizado.', 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const entregar = useMutation({ mutationFn: () => entregarEstudio(estudioId, valor.trim()), onSuccess: d => { actualizar(d); setAccion(null); setValor(''); notificar('Entrega registrada.', 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const a = detalle.adquisicion; const etapa = detalle.estudio.etapa; const permisos = detalle.permisos
  const solicitadas = proyecciones(detalle.estudio.detalle?.proyecciones_solicitadas, detalle.config); const realizadas = proyecciones(a?.proyecciones_realizadas, detalle.config)
  const observaciones = detalle.estudio.detalle?.observaciones || a?.observaciones
  const siguiente = { pendiente_realizacion: ['Registrar adquisición', 'adquisicion'], en_adquisicion: ['Continuar la adquisición', 'adquisicion'], pendiente_informe: ['Redactar informe', 'informe'], borrador: ['Continuar el informe', 'informe'] }[etapa]
  const datos = [
    ['Solicitud', <Link key="s" to={`/rayos-x/gestion/solicitudes/${detalle.solicitud.id}`}>{detalle.solicitud.referencia}</Link>],
    ['Región', detalle.config?.region],
    ['Proyecciones solicitadas', solicitadas !== 'Ninguna registrada' && solicitadas],
    ['Proyecciones realizadas', realizadas !== 'Ninguna registrada' && realizadas],
    ['Observaciones', observaciones],
  ].filter(([, v]) => v)
  return <div className="rxe-seccion">
    {etapa === 'no_realizado' ? <section className="rxe-bloque rxe-aviso-no-realizado" role="status"><strong>Estudio no realizado</strong><span>Se cerró sin tomar imágenes. El motivo queda en el historial.</span></section>
      : <section className="rxe-bloque rxe-avance-bloque"><ol className="rxe-avance" aria-label="Avance del estudio">{avanceDelFlujo(etapa).map((paso, i) => <li key={paso.id} data-estado={paso.estado} aria-current={paso.estado === 'actual' ? 'step' : undefined}>
        <span className="rxe-avance-marca" aria-hidden="true">{paso.estado === 'hecho' ? '✓' : i + 1}</span><span>{ETAPAS_TEXTO[paso.id]}<small className="rxe-sr">{paso.estado === 'hecho' ? ' (hecho)' : paso.estado === 'actual' ? ' (en curso)' : ' (pendiente)'}</small></span></li>)}</ol>
        <div className="rxe-siguiente">
          {siguiente && (permisos.registrar_adquisicion || permisos.redactar_informe) && <Boton onClick={() => irA(siguiente[1])}>{siguiente[0]}</Boton>}
          {permisos.entregar && <Boton onClick={() => setAccion('entregar')}>Registrar entrega</Boton>}
          {['validado', 'entregado'].includes(etapa) && <BotonEnlace variante="secundario" to={`/rayos-x/gestion/estudios/${estudioId}/impresion`}>Ver informe impreso</BotonEnlace>}
        </div></section>}
    <section className="rxe-bloque"><h2>Datos del estudio</h2><dl className="rxe-datos rxe-datos-resumen">{datos.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      <p className="rxe-enlaces"><Link to={`/rayos-x/gestion/pacientes/${detalle.paciente.id}`}>Ver historial radiológico del paciente</Link></p></section>
    {detalle.informes_externos?.length > 0 && <section className="rxe-bloque"><h2>Informes externos</h2><ul className="rxe-lista">{detalle.informes_externos.map(x => <li key={x.id}><div><strong>Informe externo — {x.establecimiento}</strong><span>{x.profesional || 'Profesional no informado'} · {x.fecha_informe || x.fecha_carga}</span></div></li>)}</ul></section>}
    {detalle.adendas?.length > 0 && <section className="rxe-bloque"><h2>Adendas</h2><ul className="rxe-lista">{detalle.adendas.map(x => <li key={x.id}><div><strong>{x.motivo}</strong><span>{x.autor_nombre} · {new Date(x.fecha_hora).toLocaleString('es-BO')}</span><p>{x.texto}</p></div></li>)}</ul></section>}
    {permisos.marcar_no_realizado && <p className="rxe-no-realizado"><button type="button" className="rxe-enlace-peligro" onClick={() => setAccion('no-realizado')}>Marcar este estudio como no realizado</button></p>}
    {accion && <ConfirmarAccion titulo={accion === 'entregar' ? 'Registrar entrega' : 'Marcar como no realizado'} textoConfirmar={accion === 'entregar' ? 'Registrar entrega' : 'Marcar como no realizado'} peligro={accion !== 'entregar'} pendiente={noRealizado.isPending || entregar.isPending} onCancelar={() => { setAccion(null); setValor('') }} onConfirmar={() => valor.trim() && (accion === 'entregar' ? entregar.mutate() : noRealizado.mutate())}>
      <label className="lab-search-label">{accion === 'entregar' ? 'Entregado a' : 'Motivo'} *<textarea required value={valor} onChange={e => setValor(e.target.value)} /></label>{!valor.trim() && <p className="lab-form-hint">Este dato es obligatorio.</p>}
    </ConfirmarAccion>}</div>
}

function Historial({ historial }) {
  return <section className="rxe-bloque"><h2>Historial</h2><ol className="rxe-linea-tiempo">{historial?.length ? historial.map((item, i) => <li key={`${item.fecha_hora}-${i}`}><time>{new Date(item.fecha_hora).toLocaleString('es-BO')}</time><strong>{item.descripcion}</strong><span>{item.usuario || 'Sistema'}</span></li>) : <li>No hay eventos registrados.</li>}</ol></section>
}

export default function EstudioRayosXPage({ usuario, logout }) {
  const { estudioId } = useParams(); const [params, setParams] = useSearchParams()
  const { data: detalle, isLoading, isError, error } = useQuery({ queryKey: ['radiologia', 'estudio', estudioId], queryFn: ({ signal }) => obtenerEstudio(estudioId, signal) })
  const solicitada = params.get('seccion')
  useEffect(() => { if (!detalle || SECCIONES.includes(solicitada)) return; const inicial = detalle.permisos.redactar_informe ? 'informe' : detalle.permisos.registrar_adquisicion ? 'adquisicion' : 'resumen'; setParams({ seccion: inicial }, { replace: true }) }, [detalle, solicitada, setParams])
  const seccion = SECCIONES.includes(solicitada) ? solicitada : 'resumen'
  const navegacion = { volverA: '/rayos-x/gestion', textoVolver: 'Volver a Rayos X', migas: [{ texto: 'Rayos X', ruta: '/rayos-x/gestion' }, ...(detalle ? [{ texto: detalle.solicitud.referencia, ruta: `/rayos-x/gestion/solicitudes/${detalle.solicitud.id}` }, { texto: detalle.estudio.referencia_estudio }] : [{ texto: 'Estudio' }])] }
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacion} ancho>
    {isLoading && <p>Cargando estudio...</p>}{isError && <p role="alert" className="lab-form-error">{mensajeError(error, 'No se pudo cargar el estudio.')}</p>}
    {detalle && <><header className="rxe-cabecera"><div><span className="rxe-etapa">{detalle.estudio.etapa_texto}</span><h1>{detalle.estudio.tipo_estudio_nombre}{detalle.estudio.detalle?.lateralidad ? ` · ${lateralidad(detalle.estudio.detalle.lateralidad)}` : ''}</h1><p>{detalle.estudio.referencia_estudio}</p></div><dl>
      <div><dt>Paciente</dt><dd>{detalle.paciente.nombre_completo}</dd></div><div><dt>Documento</dt><dd>{detalle.paciente.numero_documento || 'No registrado'}</dd></div><div><dt>Edad / sexo</dt><dd>{detalle.paciente.edad ?? '—'} / {detalle.paciente.sexo || '—'}</dd></div><div><dt>Solicitante</dt><dd>{detalle.solicitud.medico_solicitante || 'No registrado'}</dd></div><div><dt>Indicación clínica</dt><dd>{detalle.estudio.detalle?.indicacion_clinica || 'No registrada'}</dd></div><div><dt>Prioridad</dt><dd>{detalle.estudio.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'}</dd></div>
    </dl></header><nav className="rxe-tabs" role="tablist" aria-label="Secciones del estudio">{SECCIONES.map(tab => <button key={tab} type="button" role="tab" aria-selected={seccion === tab} onClick={() => setParams({ seccion: tab })}>{NOMBRES_SECCION[tab]}</button>)}</nav>
      {seccion === 'resumen' && <Resumen estudioId={estudioId} detalle={detalle} irA={tab => setParams({ seccion: tab })} />}{seccion === 'adquisicion' && <SeccionAdquisicion estudioId={estudioId} detalle={detalle} />}{seccion === 'informe' && <SeccionInforme estudioId={estudioId} detalle={detalle} irA={tab => setParams({ seccion: tab })} />}{seccion === 'historial' && <Historial historial={detalle.historial} />}
    </>}
  </RayosXLayout>
}
