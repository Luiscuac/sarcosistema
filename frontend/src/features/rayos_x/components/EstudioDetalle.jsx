import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { obtenerEstudio, obtenerArchivo, obtenerVista, solicitarAnalisis, obtenerAnalisis, guardarRevision } from '../api/rayosXAiApi.js'
import VisorRadiografia from './VisorRadiografia.jsx'
import PanelAsistente, { VeredictoAsistente } from './PanelAsistente.jsx'
import PanelInforme from './PanelInforme.jsx'
import { DECISIONES, enProceso, validarRevision, mensajeError, erroresAnalisis, snapshotCompatible, revisionVigente, lecturaAnormal } from '../analisis.js'

// Vista PNG generada en el servidor (DICOM, 16 bits, paleta); si no está disponible, el archivo original.
const cargarImagen = async (id, archivoId, signal) => {
  try { return await obtenerVista(id, archivoId, signal) } catch (error) {
    if (signal?.aborted) throw error
    return obtenerArchivo(id, archivoId, signal)
  }
}

// Distancia coseno del buscador documental -> relación en lenguaje simple.
const relacionEvidencia = d => typeof d !== 'number' ? { clave: 'media', texto: 'Relación media' } : d < 0.35 ? { clave: 'alta', texto: 'Relación alta' } : d < 0.5 ? { clave: 'media', texto: 'Relación media' } : { clave: 'baja', texto: 'Relación baja' }

const PESTANAS = [['hallazgos', 'Hallazgos'], ['informe', 'Informe y comparación'], ['evidencia', 'Lecturas y límites'], ['revision', 'Tu revisión']]
const OPCIONES_DECISION = [['aceptada_como_propuesta', 'Acepto'], ['corregida', 'Corrijo'], ['rechazada', 'Rechazo']]

function SolicitarAnalisis({ confirmado, setConfirmado, proyeccion, setProyeccion, deshabilitado, onAnalizar, habilitada, compacto }) {
  return <div className={`rx-ia-solicitar${compacto ? ' es-compacto' : ''}`}>
    <label className="rx-ia-check"><input type="checkbox" checked={confirmado} onChange={e => setConfirmado(e.target.checked)} /> Confirmo que es una radiografía de tórax frontal</label>
    <label className="rx-ia-campo">Proyección<select value={proyeccion} onChange={e => setProyeccion(e.target.value)}>
      <option value="PA">Posteroanterior (PA)</option><option value="AP">Anteroposterior (AP)</option><option value="frontal_no_especificada">Frontal no especificada</option>
    </select></label>
    <button type="button" className="primary-button" disabled={deshabilitado} onClick={onAnalizar}>{compacto ? 'Analizar de nuevo' : 'Analizar con IA'}</button>
    {!habilitada && <p className="rx-nota">La asistencia de IA está deshabilitada en este servidor; el informe sigue disponible.</p>}
  </div>
}

export default function EstudioDetalle({ id, usuario, habilitada, onVolver }) {
  const cache = useQueryClient()
  const [analisisId, setAnalisisId] = useState(null)
  const [confirmado, setConfirmado] = useState(false)
  const [proyeccion, setProyeccionBase] = useState('PA')
  const [clave, setClave] = useState(() => crypto.randomUUID())
  const [decision, setDecision] = useState('')
  const [motivo, setMotivo] = useState('')
  const [correccion, setCorreccion] = useState('')
  const [anormal, setAnormal] = useState('')
  const [tb, setTb] = useState('')
  const [versionBorrador, setVersionBorrador] = useState(null)
  const [url, setUrl] = useState('')
  const [mapa, setMapa] = useState(null)
  const [pestana, setPestana] = useState('hallazgos')
  const setProyeccion = valor => { setProyeccionBase(valor); setClave(crypto.randomUUID()) }
  // Sin reintentos ante 404/403: no es un fallo pasajero y dejaría la pantalla "cargando" varios segundos.
  const detalle = useQuery({ queryKey: ['imagenes', usuario.id, 'estudio', id], queryFn: ({ signal }) => obtenerEstudio(id, signal), retry: (intentos, error) => ![403, 404].includes(error?.response?.status) && intentos < 2 })
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
  const limpiarRevision = () => { setDecision(''); setMotivo(''); setCorreccion(''); setAnormal(''); setTb(''); setVersionBorrador(null) }
  const solicitar = useMutation({ mutationFn: () => solicitarAnalisis(id, { confirmar_torax_frontal: confirmado, proyeccion, clave }), onSuccess: a => { setAnalisisId(a.id); setClave(crypto.randomUUID()); limpiarRevision(); setMapa(null); setPestana('hallazgos') } })
  const revision = useMutation({ mutationFn: () => guardarRevision(analisisId, { version: versionBorrador, decision, motivo, correccion, anormal_confirmado: lecturaAnormal(anormal), tb_confirmada: lecturaAnormal(tb) }), onSuccess: a => { cache.setQueryData(['imagenes', usuario.id, 'analisis', analisisId], a); limpiarRevision() } })
  const compatible = snapshotCompatible(analisis.data, detalle.data)
  const resultado = compatible ? analisis.data?.resultado : null
  const procesando = enProceso(analisis.data?.estado)
  const conflicto = versionBorrador !== null && !revisionVigente(versionBorrador, analisis.data?.version_revision)
  const iniciarBorrador = () => { if (versionBorrador === null) setVersionBorrador(analisis.data.version_revision) }
  const puedeAnalizar = habilitada && confirmado && archivoId && !solicitar.isPending && !procesando

  if (detalle.isPending) return <p role="status">Cargando estudio…</p>
  if (detalle.error) return <section className="rx-ia"><header className="rx-ia-cabecera">{onVolver && <button type="button" className="lab-secondary-button" onClick={onVolver}>← Volver a la lista</button>}</header>
    <div className="rx-ia-tarjeta" role="alert"><h3>No se puede abrir este estudio en el asistente</h3>
      <p>{detalle.error?.response?.status === 404 ? 'El asistente de IA solo analiza radiografías de tórax con informe publicado. Este estudio no cumple esa condición; su informe sigue disponible en la ficha del paciente.' : mensajeError(detalle.error)}</p></div></section>
  const d = detalle.data
  const advertencias = resultado ? [...new Set([...(resultado.fusion.advertencias || []), ...(resultado.rag.advertencias || []), ...(resultado.vision.warnings || [])])] : []

  return <section className="rx-ia" aria-label="Asistente de IA del estudio">
    <header className="rx-ia-cabecera">
      {onVolver && <button type="button" className="lab-secondary-button" onClick={onVolver}>← Volver a la lista</button>}
      <div><p className="rx-ia-etiqueta">{d.estudio} · {d.referencia}</p><h2>{d.paciente || 'Paciente'}</h2></div>
      <span className="rx-ia-experimental">IA experimental · no diagnostica</span>
    </header>

    <div className="rx-ia-cuerpo">
      <aside className={`rx-ia-visor${procesando ? ' es-analizando' : ''}`} aria-label="Radiografía" aria-busy={procesando}>
        {imagen.isFetching && <p role="status">Cargando radiografía…</p>}
        {imagen.error && <p role="alert">{mensajeError(imagen.error)}</p>}
        {archivoId && imagen.data && url && <VisorRadiografia url={url} alt={`Radiografía del estudio ${d.referencia}`} vision={resultado?.vision} mapa={mapa} onMapa={setMapa} />}
        {!archivoId && <p>No hay archivo activo disponible.</p>}
      </aside>

      <div className="rx-ia-flujo">
        {!resultado && !procesando && <section className="rx-ia-tarjeta">
          <h3>Analizar con IA</h3>
          <p>Sugiere hallazgos, marca dónde se fijó y lo compara con el informe.</p>
          <SolicitarAnalisis {...{ confirmado, setConfirmado, proyeccion, setProyeccion, habilitada }} deshabilitado={!puedeAnalizar} onAnalizar={() => solicitar.mutate()} />
        </section>}

        {procesando && <section className="rx-ia-tarjeta rx-ia-proceso" role="status">
          <span className="rx-ia-girando" aria-hidden="true" />
          <div><h3>{analisis.data.estado === 'en_cola' ? 'En cola' : 'Analizando…'}</h3><p>Puede tardar hasta un minuto. No cierres esta pantalla.</p></div>
        </section>}

        {solicitar.error && <p role="alert" className="rx-ia-error">{mensajeError(solicitar.error)}</p>}
        {analisis.error && <p role="alert" className="rx-ia-error">{mensajeError(analisis.error)}</p>}
        {analisis.data && !compatible && <p role="alert" className="rx-ia-error">El análisis anterior corresponde a otra versión del informe o de la imagen. Solicita un análisis nuevo.</p>}
        {['error', 'interrumpido'].includes(analisis.data?.estado) && <p role="alert" className="rx-ia-error">{erroresAnalisis[analisis.data.error_codigo] || 'El análisis falló; el informe no se modificó.'}</p>}

        {resultado && <>
          <VeredictoAsistente vision={resultado.vision} prioridad={analisis.data.prioridad} />
          <nav className="rx-ia-pestanas" role="tablist" aria-label="Detalle del análisis">
            {PESTANAS.map(([clavePestana, nombre]) => <button key={clavePestana} type="button" role="tab" aria-selected={pestana === clavePestana} onClick={() => setPestana(clavePestana)}>{nombre}</button>)}
          </nav>
          <div className="rx-ia-contenido" role="tabpanel">
            {pestana === 'hallazgos' && <PanelAsistente vision={resultado.vision} mapa={mapa} onMapa={setMapa} />}

            {pestana === 'informe' && <>
              <section className="rx-ia-informe"><h4>Informe publicado</h4><p className="rx-texto">{d.informe_texto || 'No hay informe publicado disponible.'}</p></section>
              <PanelInforme fusion={resultado.fusion} mapa={mapa} onMapa={setMapa} conMapa={nombre => Boolean(resultado.vision?.mapas_calor?.mapas?.[nombre])} />
            </>}

            {pestana === 'evidencia' && <>
              <section><h4>Lecturas de apoyo</h4>
                <p className="rx-nota">Fragmentos de artículos médicos abiertos que el sistema encontró parecidos a lo que sugiere la IA. Están en inglés y sirven para consultar; no confirman nada del paciente.</p>
                {(resultado.rag.evidencia || []).length
                  ? <ul className="rx-ia-lecturas">{resultado.rag.evidencia.map(e => {
                      const relacion = relacionEvidencia(e.distancia_coseno)
                      return <li key={e.id}>
                        <div className="rx-ia-lectura-cabecera"><strong>{e.seccion?.split(' / ').pop() || 'Fragmento'}</strong><span className={`rx-ia-relacion es-${relacion.clave}`}>{relacion.texto}</span></div>
                        <small>{e.titulo}</small>
                        <div className="rx-ia-lectura-acciones">
                          <details><summary>Ver fragmento</summary><blockquote>{e.cita}</blockquote></details>
                          {/^https:\/\//.test(e.fuente || '') && <a href={e.fuente} target="_blank" rel="noopener noreferrer">Abrir artículo ↗</a>}
                        </div>
                      </li>
                    })}</ul>
                  : <p className="rx-ia-vacio">No hay lecturas de apoyo para este análisis.</p>}
              </section>
              <section><h4>Qué tener en cuenta</h4>
                <ul className="rx-ia-limites">
                  <li>Solo analiza radiografías de tórax frontales.</li>
                  <li>Sugiere parecidos, no diagnostica: un resultado bajo no descarta enfermedad.</li>
                  <li>La comparación con el informe busca palabras clave; puede no entender redacciones poco habituales.</li>
                </ul>
                <details className="rx-ia-plegable"><summary>Detalle técnico ({advertencias.length})</summary>
                  <ul className="rx-ia-limites">{advertencias.map((a, i) => <li key={i}>{a}</li>)}</ul>
                  <p className="rx-nota">{resultado.fusion.criterio_tecnico.descripcion} Punto de corte técnico: {resultado.fusion.criterio_tecnico.umbral}.</p>
                </details>
              </section>
            </>}

            {pestana === 'revision' && <>
              <p className="rx-nota">¿Coincide con tu lectura? No cambia el informe.</p>
              <form className="rx-ia-revision" onSubmit={e => { e.preventDefault(); revision.mutate() }}>
                <fieldset><legend>Tu decisión</legend>
                  <div className="rx-ia-opciones">{OPCIONES_DECISION.map(([valor, titulo]) => <label key={valor} className={decision === valor ? 'es-elegida' : undefined}>
                    <input type="radio" name="rx-decision" value={valor} checked={decision === valor} onChange={() => { iniciarBorrador(); setDecision(valor) }} />
                    <strong>{titulo}</strong></label>)}</div>
                </fieldset>
                {decision === 'corregida' && <label className="rx-ia-campo">Corrección<textarea value={correccion} maxLength={4000} onChange={e => { iniciarBorrador(); setCorreccion(e.target.value) }} placeholder="¿Qué cambiarías de la propuesta?" /></label>}
                {decision && decision !== 'aceptada_como_propuesta' && <label className="rx-ia-campo">Motivo<textarea value={motivo} maxLength={2000} onChange={e => { iniciarBorrador(); setMotivo(e.target.value) }} /></label>}
                <fieldset className="rx-ia-lectura"><legend>La radiografía es… <small>(opcional)</small></legend>
                  {[['si', 'Anormal'], ['no', 'Normal'], ['', 'Prefiero no indicarlo']].map(([valor, texto]) => <label key={texto}><input type="radio" name="rx-anormal" value={valor} checked={anormal === valor} onChange={() => { iniciarBorrador(); setAnormal(valor) }} />{texto}</label>)}
                </fieldset>
                <fieldset className="rx-ia-lectura"><legend>Tuberculosis <small>(opcional · solo con baciloscopía, GeneXpert o cultivo)</small></legend>
                  {[['si', 'Confirmada'], ['no', 'Descartada'], ['', 'Sin resultado todavía']].map(([valor, texto]) => <label key={texto}><input type="radio" name="rx-tb" value={valor} checked={tb === valor} onChange={() => { iniciarBorrador(); setTb(valor) }} />{texto}</label>)}
                </fieldset>
                {conflicto && <p role="alert" className="rx-ia-error">Otra persona guardó una revisión más reciente. Tu borrador no se guardará encima.</p>}
                <div className="rx-ia-acciones">
                  <button className="primary-button" disabled={revision.isPending || conflicto || !revisionVigente(versionBorrador, analisis.data.version_revision) || !validarRevision(decision, motivo, correccion)}>Guardar revisión</button>
                  {versionBorrador !== null && <button type="button" className="lab-secondary-button" onClick={() => { limpiarRevision(); analisis.refetch() }}>Descartar cambios</button>}
                </div>
                {revision.error && <p role="alert" className="rx-ia-error">{mensajeError(revision.error)}</p>}
                {revision.isSuccess && <p role="status" className="rx-ia-ok">Revisión guardada. El informe no cambió.</p>}
              </form>
              {(analisis.data.revisiones || []).length > 0 && <details className="rx-ia-plegable"><summary>Revisiones anteriores ({analisis.data.revisiones.length})</summary>
                <ul className="rx-ia-historial">{analisis.data.revisiones.map(r => <li key={r.version}><strong>{DECISIONES[r.decision] || 'Revisión'}</strong> · {new Date(r.fecha).toLocaleString('es-BO')}
                  {r.motivo && <p>{r.motivo}</p>}{r.correccion && <p>Corrección: {r.correccion}</p>}{r.anormal_confirmado != null && <p>Lectura: {r.anormal_confirmado ? 'anormal' : 'normal'}</p>}{r.tb_confirmada != null && <p>Tuberculosis: {r.tb_confirmada ? 'confirmada' : 'descartada'}</p>}</li>)}</ul>
              </details>}
            </>}
          </div>
          <details className="rx-ia-plegable rx-ia-nuevo"><summary>Volver a analizar</summary>
            <SolicitarAnalisis compacto {...{ confirmado, setConfirmado, proyeccion, setProyeccion, habilitada }} deshabilitado={!puedeAnalizar} onAnalizar={() => solicitar.mutate()} />
          </details>
        </>}

        {!resultado && <section className="rx-ia-tarjeta rx-ia-informe"><h3>Informe publicado</h3><p className="rx-texto">{d.informe_texto || 'No hay informe publicado disponible.'}</p></section>}
      </div>
    </div>
  </section>
}
