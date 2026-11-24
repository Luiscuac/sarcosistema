import { useEffect, useMemo, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import Dialogo from '../../../../shared/ui/Dialogo.jsx'
import { useAvisoCambiosSinGuardar } from '../../../../shared/hooks/useAvisoCambiosSinGuardar.js'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import { guardarBorradorInforme, previsualizarInforme, validarInforme } from '../../compartido/api/radiologiaApi.js'
import FormularioInforme from './FormularioInforme.jsx'
import PanelImagenes from './PanelImagenes.jsx'
import { detectarCambios, estadoInicialInforme, limpiarContenido } from '../utils/informe.js'
import Boton, { BotonEnlace } from '../../../../shared/ui/Boton.jsx'
import ResumenAvance from '../../../../shared/ui/ResumenAvance.jsx'
import { resumenInforme } from '../utils/flujo.js'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'
import { formatearFechaHora } from '../../../../shared/utils/formatearFecha.js'

function TextoInforme({ texto }) {
  return <div className="rxe-texto-informe">{texto || 'El informe aún no tiene texto.'}</div>
}

function Adendas({ adendas }) {
  return adendas.length > 0 && <section className="rxe-adendas"><h3>Adendas</h3>{adendas.map(adenda => <article key={adenda.id}><header>{formatearFechaHora(adenda.fecha_hora)} · {adenda.autor_nombre}</header><strong>{adenda.motivo}</strong><p>{adenda.texto}</p></article>)}</section>
}

function InformePublicado({ estudioId, detalle }) {
  const informe = detalle.informe
  return <div className="rxe-workspace"><PanelImagenes imagenes={detalle.imagenes || []} /><div className="rxe-work-form rxe-publicado"><p className="rxe-estado">Informe validado. Se muestra en modo de solo lectura.</p><TextoInforme texto={informe.texto} />
    <dl className="rxe-datos"><div><dt>Profesional responsable</dt><dd>{informe.responsable_nombre || 'No informado'}</dd></div><div><dt>Registro profesional</dt><dd>{informe.registro_profesional || 'No informado'}</dd></div><div><dt>Fecha de validación</dt><dd>{informe.fecha_hora_publicacion ? formatearFechaHora(informe.fecha_hora_publicacion) : 'No informada'}</dd></div></dl>
    <Adendas adendas={detalle.adendas || []} />
    <BotonEnlace className="rxe-link-boton" to={`/rayos-x/gestion/estudios/${estudioId}/impresion`}>Ver informe para imprimir</BotonEnlace>
  </div></div>
}

export default function SeccionInforme({ estudioId, detalle }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion(); const clave = ['radiologia', 'estudio', estudioId]
  const inicial = useMemo(() => estadoInicialInforme(detalle.informe, detalle.config?.plantilla), [detalle.informe, detalle.config?.plantilla])
  const [edicion, setEdicion] = useState(inicial); const [vista, setVista] = useState(null); const [confirmando, setConfirmando] = useState(false)
  const [detalleConfirmacion, setDetalleConfirmacion] = useState(null)
  const [validacion, setValidacion] = useState({ responsable_nombre: '', registro_profesional: '', confirmo: false }); const [conflicto, setConflicto] = useState(false)
  useEffect(() => { setEdicion(inicial); setVista(null); setConflicto(false) }, [inicial])
  const hayCambios = detectarCambios(edicion, inicial); useAvisoCambiosSinGuardar(hayCambios && Boolean(detalle.permisos.redactar_informe))
  const actualizar = d => queryClient.setQueryData(clave, d)
  const payload = () => ({ contenido: limpiarContenido(edicion.contenido), texto_final: edicion.textoFinal?.trim() || null, version_edicion: detalle.informe?.version_edicion ?? null })
  const guardar = useMutation({ mutationFn: () => guardarBorradorInforme(estudioId, payload()), onSuccess: d => { actualizar(d); setConflicto(false); notificar('Borrador guardado.', 'exito'); return d }, onError: e => { if (e.response?.status === 409) setConflicto(true); notificar(e.response?.status === 409 ? 'Otra persona guardó antes. Tu texto local se conserva.' : mensajeError(e), 'error') } })
  const previa = useMutation({ mutationFn: () => previsualizarInforme(estudioId, limpiarContenido(edicion.contenido)), onSuccess: d => setVista(d.texto), onError: e => notificar(mensajeError(e), 'error') })
  const validar = useMutation({ mutationFn: () => validarInforme(estudioId, { version_edicion: detalleConfirmacion?.informe?.version_edicion, responsable_nombre: validacion.responsable_nombre.trim(), registro_profesional: validacion.registro_profesional.trim() || null, confirmo: true }), onSuccess: d => { actualizar(d); setConfirmando(false); setDetalleConfirmacion(null); notificar('Informe validado.', 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const publicado = detalle.informe?.estado === 'publicado'
  if (publicado) return <InformePublicado estudioId={estudioId} detalle={detalle} />
  const faltaAdquisicion = ['pendiente_realizacion', 'en_adquisicion'].includes(detalle.estudio.etapa)
  if (faltaAdquisicion) return <div className="lab-detail-card rxe-informe-bloqueado"><strong>Todavía no se puede redactar el informe</strong><p>Primero completa la adquisición: sube las imágenes del estudio y pulsa «Completar adquisición».</p>{detalle.permisos.registrar_adquisicion && <BotonEnlace to={`/rayos-x/gestion/estudios/${estudioId}/adquisicion`}>Ir a la adquisición</BotonEnlace>}</div>
  if (!detalle.permisos.redactar_informe) return <div className="lab-detail-card"><p className="rxe-estado">Informe en modo de solo lectura.</p><TextoInforme texto={detalle.informe?.texto} /><Adendas adendas={detalle.adendas || []} /></div>
  const iniciarValidacion = async () => { try { const d = await guardar.mutateAsync(); setDetalleConfirmacion(d); setValidacion(v => ({ ...v, responsable_nombre: d.informe?.responsable_nombre || v.responsable_nombre })); setConfirmando(true) } catch { /* el aviso conserva la edicion */ } }
  const textoConfirmacion = edicion.textoFinal ?? vista ?? detalleConfirmacion?.informe?.texto ?? detalle.informe?.texto ?? ''
  const pendientes = (detalleConfirmacion || detalle).pendientes?.validacion || []
  const resumen = resumenInforme(edicion.contenido, edicion.textoFinal, (detalle.imagenes || []).length, (detalle.informes_externos || []).length > 0)
  return <div className="rxe-workspace"><PanelImagenes imagenes={detalle.imagenes || []} /><div className="rxe-work-form">
    <ResumenAvance resumen={resumen} motivoBloqueo={resumen.faltan.length ? `Para validar falta: ${resumen.faltan.join(' ')}` : null} />
    {detalle.informe?.estructurado === false && <p className="rxe-estado">Se cargó el informe antiguo como punto de partida del texto final.</p>}
    <FormularioInforme detalle={detalle} contenido={edicion.contenido} onChange={contenido => setEdicion({ ...edicion, contenido })} />
    {vista != null && <section className="rxe-previa"><h2>Vista previa</h2><TextoInforme texto={edicion.textoFinal ?? vista} />
      {edicion.textoFinal == null ? <Boton variante="secundario" onClick={() => setEdicion({ ...edicion, textoFinal: vista })}>Editar texto final</Boton> : <><label>Texto final<textarea rows="16" value={edicion.textoFinal} onChange={e => setEdicion({ ...edicion, textoFinal: e.target.value })} /></label><Boton variante="secundario" onClick={() => setEdicion({ ...edicion, textoFinal: null })}>Restablecer texto compuesto</Boton></>}
    </section>}
    {conflicto && <div className="rxe-conflicto" role="alert"><p>Otra persona guardó una versión más reciente. El contenido local sigue en pantalla.</p><Boton variante="secundario" onClick={() => queryClient.invalidateQueries({ queryKey: clave })}>Recargar desde el servidor</Boton></div>}
    <footer className="lab-area-result-actions rxe-pie">
      <span className={`rxe-estado-guardado${hayCambios ? ' es-pendiente' : ''}`} role="status">{hayCambios ? 'Cambios sin guardar' : 'Guardado'}</span>
      <Boton variante="secundario" disabled={guardar.isPending} onClick={() => guardar.mutate()}>{guardar.isPending ? 'Guardando…' : 'Guardar borrador'}</Boton>
      <Boton variante="secundario" disabled={previa.isPending} onClick={() => previa.mutate()}>Vista previa</Boton>
      {detalle.permisos.validar && <Boton disabled={guardar.isPending || validar.isPending || resumen.faltan.length > 0} title={resumen.faltan.join(' ') || undefined} onClick={iniciarValidacion}>Revisar y validar</Boton>}
    </footer>
  </div>
    {confirmando && <Dialogo titulo="Validar informe" descripcion="Después de validar no podrá modificarse." onCerrar={() => setConfirmando(false)} bloqueado={validar.isPending}>
      <div className="lab-dialog-body"><TextoInforme texto={textoConfirmacion} />{pendientes.length > 0 && <div className="rxe-pendientes" role="alert"><strong>Pendientes:</strong><ul>{pendientes.map(p => <li key={p}>{p}</li>)}</ul></div>}
        <label className="lab-search-label">Profesional responsable *<input required value={validacion.responsable_nombre} onChange={e => setValidacion({ ...validacion, responsable_nombre: e.target.value })} /></label><label className="lab-search-label">Registro profesional<input value={validacion.registro_profesional} onChange={e => setValidacion({ ...validacion, registro_profesional: e.target.value })} /></label>
        <label className="rxe-check"><input type="checkbox" checked={validacion.confirmo} onChange={e => setValidacion({ ...validacion, confirmo: e.target.checked })} />Confirmo que revisé las imágenes y el texto del informe.</label>
      </div><footer className="lab-dialog-footer"><Boton variante="secundario" onClick={() => setConfirmando(false)}>Seguir editando</Boton><Boton disabled={validar.isPending || pendientes.length > 0 || !validacion.confirmo || !validacion.responsable_nombre.trim()} onClick={() => validar.mutate()}>Confirmar validación</Boton></footer>
    </Dialogo>}
  </div>
}
