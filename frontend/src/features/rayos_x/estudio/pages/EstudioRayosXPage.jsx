import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import RayosXLayout from '../../components/RayosXLayout.jsx'
import ConfirmarAccion from '../../../laboratorio/components/ConfirmarAccion.jsx'
import { entregarEstudio, marcarNoRealizado, mensajeErrorApi, obtenerEstudio } from '../../api/radiologiaApi.js'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import SeccionAdquisicion from '../components/SeccionAdquisicion.jsx'
import SeccionInforme from '../components/SeccionInforme.jsx'
import '../../pages/rayos-x.css'
import './estudio.css'

const SECCIONES = ['resumen', 'adquisicion', 'informe', 'historial']
const NOMBRES_SECCION = { resumen: 'Resumen', adquisicion: 'Adquisición e imágenes', informe: 'Informe', historial: 'Historial' }
const lateralidad = valor => ({ derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }[valor] || 'No aplica')
const proyecciones = (codigos, config) => (codigos || []).map(c => config?.proyecciones?.find(p => p.codigo === c)?.nombre || c).join(', ') || 'Ninguna registrada'

function Resumen({ estudioId, detalle }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion(); const [accion, setAccion] = useState(null); const [valor, setValor] = useState('')
  const clave = ['radiologia', 'estudio', estudioId]; const actualizar = d => queryClient.setQueryData(clave, d)
  const noRealizado = useMutation({ mutationFn: () => marcarNoRealizado(estudioId, valor.trim()), onSuccess: d => { actualizar(d); setAccion(null); setValor(''); notificar('Estudio marcado como no realizado.', 'exito') }, onError: e => notificar(mensajeErrorApi(e), 'error') })
  const entregar = useMutation({ mutationFn: () => entregarEstudio(estudioId, valor.trim()), onSuccess: d => { actualizar(d); setAccion(null); setValor(''); notificar('Entrega registrada.', 'exito') }, onError: e => notificar(mensajeErrorApi(e), 'error') })
  const a = detalle.adquisicion
  return <div className="rxe-seccion"><section className="rxe-bloque"><h2>Resumen del estudio</h2><dl className="rxe-datos">
    <div><dt>Solicitud de origen</dt><dd><Link to={`/rayos-x/gestion/solicitudes/${detalle.solicitud.id}`}>{detalle.solicitud.referencia}</Link></dd></div>
    <div><dt>Proyecciones solicitadas</dt><dd>{proyecciones(detalle.estudio.detalle?.proyecciones_solicitadas, detalle.config)}</dd></div><div><dt>Proyecciones realizadas</dt><dd>{proyecciones(a?.proyecciones_realizadas, detalle.config)}</dd></div>
    <div><dt>Estado de adquisición</dt><dd>{a?.estado?.replaceAll('_', ' ') || 'No iniciada'}</dd></div><div className="rxe-span"><dt>Observaciones</dt><dd>{detalle.estudio.detalle?.observaciones || a?.observaciones || 'Sin observaciones'}</dd></div>
  </dl><Link to={`/rayos-x/gestion/pacientes/${detalle.paciente.id}`}>Ver historial radiológico del paciente</Link>
    <div className="rxe-acciones">{detalle.permisos.marcar_no_realizado && <button type="button" className="lab-secondary-button" onClick={() => setAccion('no-realizado')}>Marcar como no realizado</button>}{detalle.permisos.entregar && <button type="button" className="primary-button" onClick={() => setAccion('entregar')}>Registrar entrega</button>}</div>
  </section>
  <section className="rxe-bloque"><h2>Informes externos</h2>{detalle.informes_externos?.length ? <ul className="rxe-lista">{detalle.informes_externos.map(x => <li key={x.id}><div><strong>Informe externo — {x.establecimiento}</strong><span>{x.profesional || 'Profesional no informado'} · {x.fecha_informe || x.fecha_carga}</span></div></li>)}</ul> : <p>No hay informes externos.</p>}</section>
  <section className="rxe-bloque"><h2>Adendas</h2>{detalle.adendas?.length ? <ul className="rxe-lista">{detalle.adendas.map(x => <li key={x.id}><div><strong>{x.motivo}</strong><span>{x.autor_nombre} · {new Date(x.fecha_hora).toLocaleString('es-BO')}</span><p>{x.texto}</p></div></li>)}</ul> : <p>No hay adendas.</p>}</section>
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
    {isLoading && <p>Cargando estudio...</p>}{isError && <p role="alert" className="lab-form-error">{mensajeErrorApi(error, 'No se pudo cargar el estudio.')}</p>}
    {detalle && <><header className="rxe-cabecera"><div><span className="rxe-etapa">{detalle.estudio.etapa_texto}</span><h1>{detalle.estudio.tipo_estudio_nombre} · {lateralidad(detalle.estudio.detalle?.lateralidad)}</h1><p>{detalle.estudio.referencia_estudio}</p></div><dl>
      <div><dt>Paciente</dt><dd>{detalle.paciente.nombre_completo}</dd></div><div><dt>Documento</dt><dd>{detalle.paciente.numero_documento || 'No registrado'}</dd></div><div><dt>Edad / sexo</dt><dd>{detalle.paciente.edad ?? '—'} / {detalle.paciente.sexo || '—'}</dd></div><div><dt>Solicitante</dt><dd>{detalle.solicitud.medico_solicitante || 'No registrado'}</dd></div><div><dt>Indicación clínica</dt><dd>{detalle.estudio.detalle?.indicacion_clinica || 'No registrada'}</dd></div><div><dt>Prioridad</dt><dd>{detalle.estudio.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'}</dd></div>
    </dl></header><nav className="rxe-tabs" role="tablist" aria-label="Secciones del estudio">{SECCIONES.map(tab => <button key={tab} type="button" role="tab" aria-selected={seccion === tab} onClick={() => setParams({ seccion: tab })}>{NOMBRES_SECCION[tab]}</button>)}</nav>
      {seccion === 'resumen' && <Resumen estudioId={estudioId} detalle={detalle} />}{seccion === 'adquisicion' && <SeccionAdquisicion estudioId={estudioId} detalle={detalle} />}{seccion === 'informe' && <SeccionInforme estudioId={estudioId} detalle={detalle} />}{seccion === 'historial' && <Historial historial={detalle.historial} />}
    </>}
  </RayosXLayout>
}
