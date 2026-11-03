import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { guardarBorradorArea, obtenerExamen, obtenerSolicitud, publicarResultadosArea } from '../api/laboratorioApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import { agruparPorCategoria } from '../utils/agruparSolicitudes.js'
import './laboratorio.css'
import './area-resultados.css'

export default function AreaResultadosPage({ usuario, logout }) {
  const { solicitudId, areaCodigo } = useParams()
  const queryClient = useQueryClient()
  const [valores, setValores] = useState({})
  const [observaciones, setObservaciones] = useState('')
  const [observacionesActivas, setObservacionesActivas] = useState(false)
  const [responsable, setResponsable] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [publicando, setPublicando] = useState(false)
  const { data: solicitud, isLoading, isError } = useQuery({
    queryKey: ['laboratorio', 'solicitud', solicitudId],
    queryFn: () => obtenerSolicitud(solicitudId),
  })
  const area = solicitud && agruparPorCategoria(solicitud.estudios).find((grupo) => grupo.codigo === areaCodigo)
  const listos = area?.estudios.filter((estudio) => ['resultado_en_preparacion', 'publicado'].includes(estudio.estado)) ?? []
  const pendientes = area?.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra') ?? []
  const noRealizados = area?.estudios.filter((estudio) => estudio.estado === 'no_realizado') ?? []
  const estudiosQuery = useQuery({
    queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo, listos.map((estudio) => estudio.estudio_id)],
    queryFn: async () => Promise.all(listos.map((estudio) => obtenerExamen(estudio.estudio_id))),
    enabled: listos.length > 0,
  })
  const resultados = estudiosQuery.data ?? []
  const resultadosEditables = resultados.filter((resultado) => resultado.estado_resultado !== 'publicado')
  const publicados = resultados.length > 0 && resultadosEditables.length === 0
  const hayCambios = useMemo(() => resultados.some((resultado) =>
    (resultado.parametros ?? []).some((parametro) => (valores[parametro.id] ?? parametro.valor ?? '') !== (parametro.valor ?? '')),
  ) || observaciones !== (resultados[0]?.observaciones ?? '') || responsable !== (resultados[0]?.responsable_analisis ?? ''),
  [resultados, valores, observaciones, responsable])

  useEffect(() => {
    if (!resultados.length) return
    setValores(Object.fromEntries(resultados.flatMap((resultado) => resultado.parametros.map((parametro) => [parametro.id, parametro.valor ?? '']))))
    setObservaciones(resultados[0].observaciones ?? '')
    setObservacionesActivas(Boolean(resultados[0].observaciones?.trim()))
    setResponsable(resultados[0].responsable_analisis ?? resultados[0].responsable_publicacion ?? '')
  }, [resultados])

  async function guardarArea(event) {
    event.preventDefault()
    setError('')
    setMensaje('')
    setGuardando(true)
    try {
      await guardarBorradorArea(solicitudId, areaCodigo, {
        estudios: resultadosEditables.map((resultado) => ({
          estudio_id: resultado.estudio_id,
          valores: resultado.parametros.map((parametro) => ({
            parametro_id: parametro.id,
            valor: valores[parametro.id] || null,
          })),
        })),
        observaciones: observacionesActivas ? observaciones : '',
        responsable: responsable.trim(),
      })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo] }),
        queryClient.invalidateQueries({ queryKey: ['resultado'] }),
        queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud', solicitudId] }),
      ])
      setMensaje('Borrador del área guardado.')
    } catch (cause) {
      setError(cause.response?.data?.detail || 'No se pudo guardar el borrador del área.')
      await queryClient.invalidateQueries({ queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo] })
    } finally {
      setGuardando(false)
    }
  }

  async function publicarArea() {
    setError('')
    setMensaje('')
    setPublicando(true)
    try {
      await publicarResultadosArea(solicitudId, areaCodigo, {
        estudio_ids: resultadosEditables.map((resultado) => resultado.estudio_id),
        responsable: responsable.trim(),
      })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo] }),
        queryClient.invalidateQueries({ queryKey: ['resultado'] }),
        queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud', solicitudId] }),
        queryClient.invalidateQueries({ queryKey: ['examenes'] }),
      ])
      setMensaje('Resultados del área publicados.')
    } catch (cause) {
      setError(cause.response?.data?.detail || 'No se pudieron publicar todos los resultados del área.')
      await queryClient.invalidateQueries({ queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo] })
    } finally {
      setPublicando(false)
    }
  }

  const busy = guardando || publicando

  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-area-results-page">
        <Link className="lab-back-link" to={`/laboratorio/solicitudes/${solicitudId}`}>← Volver a la solicitud</Link>
        {isLoading && <p>Cargando estudios del área…</p>}
        {isError && <p role="alert">No se pudo cargar la solicitud. Vuelve a intentarlo.</p>}
        {solicitud && !area && <p role="alert">Esta solicitud no tiene estudios en el área indicada.</p>}
        {area && <>
          <header className="lab-area-results-header">
            <p className="lab-eyebrow">CAPTURA DE RESULTADOS · {solicitud.referencia}</p>
            <h1>{area.nombre}</h1>
            <p>{solicitud.paciente_nombre} · {area.estudios.length} {area.estudios.length === 1 ? 'estudio' : 'estudios'}</p>
          </header>
          {pendientes.length > 0 && <div className="lab-area-pending">
            <strong>Pendientes de muestra</strong>
            <p>Registra la muestra desde la solicitud antes de capturar estos resultados: {pendientes.map((estudio) => estudio.tipo_estudio_nombre).join(', ')}.</p>
          </div>}
          {noRealizados.length > 0 && <div className="lab-area-pending">
            <strong>Estudios no realizados</strong>
            <p>{noRealizados.map((estudio) => estudio.tipo_estudio_nombre).join(', ')}. La justificación registrada se incluirá en el informe final.</p>
          </div>}
          {estudiosQuery.isLoading && <p>Cargando formatos de resultados…</p>}
          {estudiosQuery.isError && <p role="alert">No se pudieron cargar los formatos de resultados.</p>}
          {resultados.length > 0 && <form className="lab-area-result-form" onSubmit={guardarArea}>
            {resultados.map((resultado) => {
              const secciones = resultado.parametros.reduce((grupos, parametro) => {
                const nombre = parametro.seccion || 'Resultado'
                grupos[nombre] ??= []
                grupos[nombre].push(parametro)
                return grupos
              }, {})
              return <section className="lab-area-study" key={resultado.estudio_id}>
                <header><h2>{resultado.tipo_estudio_nombre}</h2><small>{resultado.referencia_estudio}</small></header>
                {resultado.estado_resultado === 'publicado' && <p className="lab-area-study-status">Publicado</p>}
                {Object.entries(secciones).map(([seccion, parametros]) => <section className="lab-area-parameter-section" key={seccion}>
                  <h3>{seccion}</h3><div className="lab-form-grid">
                    {parametros.filter((parametro) => parametro.codigo !== 'unidad_reportada').map((parametro) => <label className="lab-result-field" key={parametro.id}>
                      {parametro.nombre}{parametro.obligatorio ? ' *' : ''}
                      {parametro.opciones?.length ? <select value={valores[parametro.id] ?? ''} disabled={publicados || busy} onChange={(event) => setValores((actual) => ({ ...actual, [parametro.id]: event.target.value }))}><option value="">Seleccionar resultado</option>{parametro.opciones.map((opcion) => <option key={opcion} value={opcion}>{opcion}</option>)}</select> : <input type={['decimal', 'entero'].includes(parametro.tipo_entrada) ? 'number' : 'text'} step={parametro.tipo_entrada === 'decimal' ? 'any' : parametro.tipo_entrada === 'entero' ? '1' : undefined} value={valores[parametro.id] ?? ''} disabled={publicados || busy} onChange={(event) => setValores((actual) => ({ ...actual, [parametro.id]: event.target.value }))} />}
                      {(parametro.unidad || parametro.rango_referencia) && <small>{[parametro.unidad, parametro.rango_referencia].filter(Boolean).join(' · ')}</small>}
                    </label>)}
                  </div>
                </section>)}
              </section>
            })}
            <div className="lab-area-meta-fields">
              <label className="lab-search-label">Profesional responsable del área
                <input required minLength={2} maxLength={200} value={responsable} onChange={(event) => setResponsable(event.target.value)} disabled={publicados || busy} placeholder="Nombre y apellido" />
              </label>
              <div className="lab-area-observations">
                <label className="lab-area-observations-toggle"><input type="checkbox" checked={observacionesActivas} onChange={(event) => setObservacionesActivas(event.target.checked)} disabled={publicados || busy} /> Agregar observaciones</label>
                {observacionesActivas && <label className="lab-search-label">Observaciones generales del área
                  <textarea value={observaciones} onChange={(event) => setObservaciones(event.target.value)} disabled={publicados || busy} maxLength={4000} rows={3} />
                </label>}
              </div>
            </div>
            {error && <p className="lab-form-error" role="alert">{error}</p>}
            {mensaje && <p className="lab-form-hint" role="status">{mensaje}</p>}
            {!publicados && <footer className="lab-area-result-actions">
              <button type="submit" disabled={busy || !responsable.trim() || !hayCambios}>{guardando ? 'Guardando…' : 'Guardar borrador del área'}</button>
              <button className="primary-button" type="button" disabled={busy || resultadosEditables.length === 0 || !resultadosEditables.every((resultado) => resultado.estado_resultado === 'borrador') || hayCambios || responsable.trim().length < 2} onClick={publicarArea}>{publicando ? 'Publicando…' : 'Publicar resultados del área'}</button>
            </footer>}
          </form>}
        </>}
      </section>
    </div>
  </main>
}
