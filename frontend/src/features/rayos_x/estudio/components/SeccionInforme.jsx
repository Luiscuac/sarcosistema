import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Dialogo from '../../../laboratorio/components/Dialogo.jsx'
import VisorRadiografia from '../../components/VisorRadiografia.jsx'
import { useAvisoCambiosSinGuardar } from '../../../../shared/hooks/useAvisoCambiosSinGuardar.js'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import { guardarBorradorInforme, mensajeErrorApi, previsualizarInforme, validarInforme } from '../../api/radiologiaApi.js'
import FormularioInforme from './FormularioInforme.jsx'
import { useVistaImagen } from './GaleriaImagenes.jsx'
import { detectarCambios, estadoInicialInforme, limpiarContenido } from '../utils/informe.js'

function BotonMiniatura({ imagen, activa, onClick }) {
  const url = useVistaImagen(imagen.archivo_id)
  return <button type="button" role="tab" aria-selected={activa} className={`rxe-tira-item${activa ? ' is-active' : ''}`} onClick={onClick}>
    {url ? <img src={url} alt="" /> : <span>...</span>}<small>{imagen.proyeccion_codigo || 'Sin asignar'}</small>
  </button>
}

function PanelImagenes({ imagenes }) {
  const [indice, setIndice] = useState(0); const tira = useRef(null)
  useEffect(() => { if (indice >= imagenes.length) setIndice(Math.max(0, imagenes.length - 1)) }, [imagenes.length, indice])
  const seleccionada = imagenes[indice]; const url = useVistaImagen(seleccionada?.archivo_id)
  const teclado = e => { if (!['ArrowLeft', 'ArrowRight'].includes(e.key) || !imagenes.length) return; e.preventDefault(); setIndice(i => e.key === 'ArrowRight' ? (i + 1) % imagenes.length : (i - 1 + imagenes.length) % imagenes.length) }
  return <aside className="rxe-work-visor"><div ref={tira} className="rxe-tira" role="tablist" aria-label="Imágenes del estudio" onKeyDown={teclado}>
    {imagenes.map((imagen, i) => <BotonMiniatura key={imagen.id} imagen={imagen} activa={i === indice} onClick={() => setIndice(i)} />)}
  </div><div className="rxe-visor-principal">{seleccionada && url ? <VisorRadiografia url={url} alt={seleccionada.nombre_original} vision={undefined} mapa={null} onMapa={() => {}} /> : <p role={url === false ? 'alert' : undefined}>{imagenes.length ? (url === false ? 'No se pudo cargar la imagen.' : 'Cargando imagen…') : 'No hay imágenes disponibles.'}</p>}</div></aside>
}

function TextoInforme({ texto }) {
  return <div className="rxe-texto-informe">{texto || 'El informe aún no tiene texto.'}</div>
}

function Adendas({ adendas }) {
  return adendas.length > 0 && <section className="rxe-adendas"><h3>Adendas</h3>{adendas.map(adenda => <article key={adenda.id}><header>{new Date(adenda.fecha_hora).toLocaleString('es-BO')} · {adenda.autor_nombre}</header><strong>{adenda.motivo}</strong><p>{adenda.texto}</p></article>)}</section>
}

function InformePublicado({ estudioId, detalle }) {
  const informe = detalle.informe
  return <div className="rxe-workspace"><PanelImagenes imagenes={detalle.imagenes || []} /><div className="rxe-work-form rxe-publicado"><p className="rxe-estado">Informe validado. Se muestra en modo de solo lectura.</p><TextoInforme texto={informe.texto} />
    <dl className="rxe-datos"><div><dt>Profesional responsable</dt><dd>{informe.responsable_nombre || 'No informado'}</dd></div><div><dt>Registro profesional</dt><dd>{informe.registro_profesional || 'No informado'}</dd></div><div><dt>Fecha de validación</dt><dd>{informe.fecha_hora_publicacion ? new Date(informe.fecha_hora_publicacion).toLocaleString('es-BO') : 'No informada'}</dd></div></dl>
    <Adendas adendas={detalle.adendas || []} />
    <Link className="primary-button rxe-link-boton" to={`/rayos-x/gestion/estudios/${estudioId}/impresion`}>Ver informe para imprimir</Link>
  </div></div>
}

export default function SeccionInforme({ estudioId, detalle, irA }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion(); const clave = ['radiologia', 'estudio', estudioId]
  const inicial = useMemo(() => estadoInicialInforme(detalle.informe, detalle.config?.plantilla), [detalle.informe, detalle.config?.plantilla])
  const [edicion, setEdicion] = useState(inicial); const [vista, setVista] = useState(null); const [confirmando, setConfirmando] = useState(false)
  const [detalleConfirmacion, setDetalleConfirmacion] = useState(null)
  const [validacion, setValidacion] = useState({ responsable_nombre: '', registro_profesional: '', confirmo: false }); const [conflicto, setConflicto] = useState(false)
  useEffect(() => { setEdicion(inicial); setVista(null); setConflicto(false) }, [inicial])
  const hayCambios = detectarCambios(edicion, inicial); useAvisoCambiosSinGuardar(hayCambios && Boolean(detalle.permisos.redactar_informe))
  const actualizar = d => queryClient.setQueryData(clave, d)
  const payload = () => ({ contenido: limpiarContenido(edicion.contenido), texto_final: edicion.textoFinal?.trim() || null, version_edicion: detalle.informe?.version_edicion ?? null })
  const guardar = useMutation({ mutationFn: () => guardarBorradorInforme(estudioId, payload()), onSuccess: d => { actualizar(d); setConflicto(false); notificar('Borrador guardado.', 'exito'); return d }, onError: e => { if (e.response?.status === 409) setConflicto(true); notificar(e.response?.status === 409 ? 'Otra persona guardó antes. Tu texto local se conserva.' : mensajeErrorApi(e), 'error') } })
  const previa = useMutation({ mutationFn: () => previsualizarInforme(estudioId, limpiarContenido(edicion.contenido)), onSuccess: d => setVista(d.texto), onError: e => notificar(mensajeErrorApi(e), 'error') })
  const validar = useMutation({ mutationFn: () => validarInforme(estudioId, { version_edicion: detalleConfirmacion?.informe?.version_edicion, responsable_nombre: validacion.responsable_nombre.trim(), registro_profesional: validacion.registro_profesional.trim() || null, confirmo: true }), onSuccess: d => { actualizar(d); setConfirmando(false); setDetalleConfirmacion(null); notificar('Informe validado.', 'exito') }, onError: e => notificar(mensajeErrorApi(e), 'error') })
  const publicado = detalle.informe?.estado === 'publicado'
  if (publicado) return <InformePublicado estudioId={estudioId} detalle={detalle} />
  const faltaAdquisicion = ['pendiente_realizacion', 'en_adquisicion'].includes(detalle.estudio.etapa)
  if (faltaAdquisicion) return <div className="rxe-bloque rxe-informe-bloqueado"><strong>Todavía no se puede redactar el informe</strong><p>Primero completa la adquisición: sube las imágenes del estudio y pulsa «Completar adquisición».</p>{irA && detalle.permisos.registrar_adquisicion && <button type="button" className="primary-button" onClick={() => irA('adquisicion')}>Ir a Adquisición e imágenes</button>}</div>
  if (!detalle.permisos.redactar_informe) return <div className="rxe-bloque"><p className="rxe-estado">Informe en modo de solo lectura.</p><TextoInforme texto={detalle.informe?.texto} /><Adendas adendas={detalle.adendas || []} /></div>
  const iniciarValidacion = async () => { try { const d = await guardar.mutateAsync(); setDetalleConfirmacion(d); setValidacion(v => ({ ...v, responsable_nombre: d.informe?.responsable_nombre || v.responsable_nombre })); setConfirmando(true) } catch { /* el aviso conserva la edicion */ } }
  const textoConfirmacion = edicion.textoFinal ?? vista ?? detalleConfirmacion?.informe?.texto ?? detalle.informe?.texto ?? ''
  const pendientes = (detalleConfirmacion || detalle).pendientes?.validacion || []
  return <div className="rxe-workspace"><PanelImagenes imagenes={detalle.imagenes || []} /><div className="rxe-work-form">
    {detalle.informe?.estructurado === false && <p className="rxe-estado">Se cargó el informe antiguo como punto de partida del texto final.</p>}
    <FormularioInforme detalle={detalle} contenido={edicion.contenido} onChange={contenido => setEdicion({ ...edicion, contenido })} />
    {vista != null && <section className="rxe-previa"><h2>Vista previa</h2><TextoInforme texto={edicion.textoFinal ?? vista} />
      {edicion.textoFinal == null ? <button type="button" className="lab-secondary-button" onClick={() => setEdicion({ ...edicion, textoFinal: vista })}>Editar texto final</button> : <><label>Texto final<textarea rows="16" value={edicion.textoFinal} onChange={e => setEdicion({ ...edicion, textoFinal: e.target.value })} /></label><button type="button" className="lab-secondary-button" onClick={() => setEdicion({ ...edicion, textoFinal: null })}>Restablecer texto compuesto</button></>}
    </section>}
    {conflicto && <div className="rxe-conflicto" role="alert"><p>Otra persona guardó una versión más reciente. El contenido local sigue en pantalla.</p><button type="button" className="lab-secondary-button" onClick={() => queryClient.invalidateQueries({ queryKey: clave })}>Recargar desde el servidor</button></div>}
  </div><footer className="rxe-barra-acciones"><strong>{hayCambios ? 'Cambios sin guardar' : 'Guardado'}</strong><button type="button" className="lab-secondary-button" disabled={guardar.isPending} onClick={() => guardar.mutate()}>Guardar borrador</button><button type="button" className="lab-secondary-button" disabled={previa.isPending} onClick={() => previa.mutate()}>Vista previa</button>{detalle.permisos.validar && <button type="button" className="primary-button" disabled={guardar.isPending || validar.isPending} onClick={iniciarValidacion}>Validar informe</button>}</footer>
    {confirmando && <Dialogo titulo="Validar informe" descripcion="Después de validar no podrá modificarse." onCerrar={() => setConfirmando(false)} bloqueado={validar.isPending}>
      <div className="lab-dialog-body"><TextoInforme texto={textoConfirmacion} />{pendientes.length > 0 && <div className="rxe-pendientes" role="alert"><strong>Pendientes:</strong><ul>{pendientes.map(p => <li key={p}>{p}</li>)}</ul></div>}
        <label className="lab-search-label">Profesional responsable *<input required value={validacion.responsable_nombre} onChange={e => setValidacion({ ...validacion, responsable_nombre: e.target.value })} /></label><label className="lab-search-label">Registro profesional<input value={validacion.registro_profesional} onChange={e => setValidacion({ ...validacion, registro_profesional: e.target.value })} /></label>
        <label className="rxe-check"><input type="checkbox" checked={validacion.confirmo} onChange={e => setValidacion({ ...validacion, confirmo: e.target.checked })} />Confirmo que revisé las imágenes y el texto del informe.</label>
      </div><footer className="lab-dialog-footer"><button type="button" className="lab-secondary-button" onClick={() => setConfirmando(false)}>Seguir editando</button><button type="button" className="primary-button" disabled={validar.isPending || pendientes.length > 0 || !validacion.confirmo || !validacion.responsable_nombre.trim()} onClick={() => validar.mutate()}>Confirmar validación</button></footer>
    </Dialogo>}
  </div>
}
