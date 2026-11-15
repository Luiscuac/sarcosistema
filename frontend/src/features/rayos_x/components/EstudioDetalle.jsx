import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { obtenerEstudio, obtenerArchivo, obtenerVista, solicitarAnalisis, obtenerAnalisis, guardarRevision } from '../api/rayosXAiApi.js'
import VisorRadiografia from './VisorRadiografia.jsx'
import PanelAsistente from './PanelAsistente.jsx'
import PanelInforme from './PanelInforme.jsx'
import { enProceso, validarRevision, mensajeError, erroresAnalisis, snapshotCompatible, revisionVigente, lecturaAnormal } from '../analisis.js'


// Vista PNG generada en el servidor (DICOM, 16 bits, paleta); si no está disponible, el archivo original.
const cargarImagen = async (id, archivoId, signal) => {
  try { return await obtenerVista(id, archivoId, signal) } catch (error) {
    if (signal?.aborted) throw error
    return obtenerArchivo(id, archivoId, signal)
  }
}
export default function EstudioDetalle({ id, usuario, habilitada }) {
  const cache = useQueryClient()
  const [analisisId, setAnalisisId] = useState(null)
  const [confirmado, setConfirmado] = useState(false)
  const [proyeccion, setProyeccion] = useState('PA')
  const [clave, setClave] = useState(() => crypto.randomUUID())
  const [decision, setDecision] = useState('')
  const [motivo, setMotivo] = useState('')
  const [correccion, setCorreccion] = useState('')
  const [anormal, setAnormal] = useState('')
  const [versionBorrador, setVersionBorrador] = useState(null)
  const [url, setUrl] = useState('')
  const [mapa, setMapa] = useState(null)
  const detalle = useQuery({ queryKey: ['imagenes', usuario.id, 'estudio', id], queryFn: ({ signal }) => obtenerEstudio(id, signal) })
  const archivoId = detalle.data?.archivo?.id
  const imagen = useQuery({ queryKey: ['imagenes', usuario.id, 'archivo', id, archivoId], queryFn: ({ signal }) => cargarImagen(id, archivoId, signal), enabled: Boolean(archivoId), gcTime: 0, staleTime: 0 })
  useEffect(() => {
    if (!imagen.data) { setUrl(''); return }
    const objectUrl = URL.createObjectURL(imagen.data)
    setUrl(objectUrl)
    return () => { URL.revokeObjectURL(objectUrl) }
  }, [imagen.data])
  useEffect(() => {
    if (!analisisId && detalle.data?.analisis_reciente) setAnalisisId(detalle.data.analisis_reciente)
  }, [analisisId, detalle.data?.analisis_reciente])
  const analisis = useQuery({ queryKey: ['imagenes', usuario.id, 'analisis', analisisId], queryFn: ({ signal }) => obtenerAnalisis(analisisId, signal), enabled: Boolean(analisisId), refetchInterval: q => enProceso(q.state.data?.estado) ? 2000 : false })
  const solicitar = useMutation({ mutationFn: () => solicitarAnalisis(id, { confirmar_torax_frontal: confirmado, proyeccion, clave }), onSuccess: a => { setAnalisisId(a.id); setClave(crypto.randomUUID()); setDecision(''); setMotivo(''); setCorreccion(''); setAnormal(''); setVersionBorrador(null) } })
  const revision = useMutation({ mutationFn: () => guardarRevision(analisisId, { version: versionBorrador, decision, motivo, correccion, anormal_confirmado: lecturaAnormal(anormal) }), onSuccess: a => { cache.setQueryData(['imagenes', usuario.id, 'analisis', analisisId], a); setDecision(''); setMotivo(''); setCorreccion(''); setAnormal(''); setVersionBorrador(null) } })
  const compatible = snapshotCompatible(analisis.data, detalle.data)
  const resultado = compatible ? analisis.data?.resultado : null
  const conflicto = versionBorrador !== null && !revisionVigente(versionBorrador, analisis.data?.version_revision)
  const iniciarBorrador = () => { if (versionBorrador === null) setVersionBorrador(analisis.data.version_revision) }
  if (detalle.isPending) return <p role="status">Cargando detalle…</p>
  if (detalle.error) return <p role="alert">{mensajeError(detalle.error)}</p>
  return <section className="rx-detalle" aria-label="Detalle del estudio">
    <h2>{detalle.data.referencia} · {detalle.data.estudio}</h2>
    <div className="rx-columnas"><div>
      <h3>Radiografía local</h3>
      {imagen.isFetching && <p role="status">Cargando radiografía…</p>}
      {imagen.error && <p role="alert">{mensajeError(imagen.error)}</p>}
      {archivoId && imagen.data && url && <VisorRadiografia url={url} alt={`Radiografía del estudio ${detalle.data.referencia}`} vision={resultado?.vision} mapa={mapa} onMapa={setMapa} />}
      {!archivoId && <p>No hay archivo activo disponible.</p>}
    </div><div><h3>Informe publicado · solo lectura</h3><p className="rx-texto">{detalle.data.informe_texto || 'No hay informe publicado disponible.'}</p><p>No se modificará al analizar ni al revisar propuestas.</p></div></div>
    <div className="rx-solicitud"><label><input type="checkbox" checked={confirmado} onChange={e => setConfirmado(e.target.checked)} /> Confirmo que es una radiografía de tórax frontal</label><label>Proyección <select value={proyeccion} onChange={e => { setProyeccion(e.target.value); setClave(crypto.randomUUID()) }}><option value="PA">PA</option><option value="AP">AP</option><option value="frontal_no_especificada">Frontal no especificada</option></select></label>
      <button type="button" className="primary-button" disabled={!habilitada || !confirmado || !archivoId || solicitar.isPending || enProceso(analisis.data?.estado)} onClick={() => solicitar.mutate()}>Analizar con IA local</button>
      {!habilitada && <p>La asistencia de IA local está deshabilitada; el informe sigue disponible.</p>}
    </div>
    {solicitar.error && <p role="alert">{mensajeError(solicitar.error)}</p>}
    {analisis.error && <p role="alert">{mensajeError(analisis.error)}</p>}
    {analisis.data && !compatible && <p role="alert">El análisis pertenece a otra versión del informe o archivo. No se mostrará junto al estudio actual; solicita un análisis nuevo.</p>}
    {enProceso(analisis.data?.estado) && <p role="status">{analisis.data.estado === 'en_cola' ? 'Análisis en cola' : 'Analizando localmente'} · puede tardar varios minutos. No cierres el servidor.</p>}
    {['error', 'interrumpido'].includes(analisis.data?.estado) && <p role="alert">{erroresAnalisis[analisis.data.error_codigo] || 'El análisis local falló; el informe clínico no se modificó.'}</p>}
    {resultado && <>
      <PanelAsistente vision={resultado.vision} mapa={mapa} onMapa={setMapa} />
      <PanelInforme fusion={resultado.fusion} mapa={mapa} onMapa={setMapa} conMapa={nombre => Boolean(resultado.vision?.mapas_calor?.mapas?.[nombre])} />
      <p>{resultado.fusion.criterio_tecnico.descripcion} Umbral técnico: {resultado.fusion.criterio_tecnico.umbral}.</p>
      <h3>Evidencia documental local</h3><p>{resultado.rag.mensaje}</p>
      {(resultado.rag.evidencia || []).map(e => <details key={e.id}><summary>{e.titulo} · {e.seccion}</summary><blockquote>{e.cita}</blockquote><p>Referencia original: {e.fuente}</p><small>Documento {e.documento_id}; caracteres {e.inicio}–{e.fin}; SHA-256 {e.sha256}</small></details>)}
      <details className="rx-advertencias"><summary>Límites del asistente ({[...(resultado.fusion.advertencias || []), ...(resultado.rag.advertencias || []), ...(resultado.vision.warnings || [])].length})</summary>
        {[...new Set([...(resultado.fusion.advertencias || []), ...(resultado.rag.advertencias || []), ...(resultado.vision.warnings || [])])].map((a, i) => <p className="rx-advertencia" key={i}>{a}</p>)}
      </details>
      <h3>Revisión médica de la propuesta</h3><p>Guardar una revisión no publica un diagnóstico ni modifica el informe.</p>
      <form onSubmit={e => { e.preventDefault(); revision.mutate() }}>
        <label htmlFor="rx-decision">Decisión</label><select id="rx-decision" value={decision} onChange={e => { iniciarBorrador(); setDecision(e.target.value) }}><option value="">Selecciona una decisión</option><option value="aceptada_como_propuesta">Aceptar como propuesta experimental</option><option value="corregida">Corregir propuesta</option><option value="rechazada">Rechazar propuesta</option></select>
        <label htmlFor="rx-motivo">Motivo</label><textarea id="rx-motivo" value={motivo} maxLength={2000} onChange={e => { iniciarBorrador(); setMotivo(e.target.value) }} />
        <fieldset className="rx-lectura"><legend>Según tu lectura, ¿la radiografía es anormal?</legend>
          {[['si', 'Sí, anormal'], ['no', 'No, normal'], ['', 'No lo indico']].map(([valor, texto]) => <label key={texto}><input type="radio" name="rx-anormal" value={valor} checked={anormal === valor} onChange={() => { iniciarBorrador(); setAnormal(valor) }} />{texto}</label>)}
          <small>Opcional. Sirve para medir y calibrar el asistente en este hospital; no publica ni modifica el informe.</small>
        </fieldset>
        {decision === 'corregida' && <><label htmlFor="rx-correccion">Corrección de la propuesta</label><textarea id="rx-correccion" value={correccion} maxLength={4000} onChange={e => { iniciarBorrador(); setCorreccion(e.target.value) }} /></>}
        <button className="primary-button" disabled={revision.isPending || conflicto || !revisionVigente(versionBorrador, analisis.data.version_revision) || !validarRevision(decision, motivo, correccion)}>Guardar revisión explícita</button>
      </form>
      {conflicto && <p role="alert">Hay una revisión más reciente. Tu borrador conserva su versión original y no se guardará encima.</p>}
      <button type="button" className="lab-secondary-button" onClick={() => { if (window.confirm('¿Descartar el borrador y cargar la revisión actual?')) { setDecision(''); setMotivo(''); setCorreccion(''); setAnormal(''); setVersionBorrador(null); analisis.refetch() } }}>Descartar borrador y recargar revisión</button>
      {revision.error && <p role="alert">{mensajeError(revision.error)}</p>}{revision.isSuccess && <p role="status">Revisión guardada; el informe clínico permanece sin cambios.</p>}
      <h4>Historial de revisiones</h4><ul>{(analisis.data.revisiones || []).map(r => <li key={r.version}>Versión {r.version}: {r.decision} · {new Date(r.fecha).toLocaleString('es-BO')} · actor {r.usuario_id}<p>{r.motivo}</p>{r.correccion && <p>{r.correccion}</p>}{r.anormal_confirmado != null && <p>Lectura del médico: {r.anormal_confirmado ? 'anormal' : 'normal'}</p>}</li>)}</ul>
    </>}
  </section>
}
