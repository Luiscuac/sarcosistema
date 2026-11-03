import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { guardarBorrador, obtenerExamen, publicarResultado } from '../api/laboratorioApi.js'
import './resultados/ResultadoEstudio.css'

function mensajeError(error) {
  const detail = error.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).filter(Boolean).join('. ') || 'Revisa los campos del resultado.'
  }
  if (error.response) {
    return 'No se pudo completar la acción. Revisa los datos e inténtalo de nuevo.'
  }
  if (error.request) {
    return 'No hay conexión con el sistema. Vuelve a intentarlo en unos momentos.'
  }
  return error.message || 'No se pudo guardar el resultado.'
}

export default function ResultadoEstudio({ estudioId, enArea = false }) {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['resultado', estudioId],
    queryFn: () => obtenerExamen(estudioId),
  })
  const [observacionesCambio, setObservacionesCambio] = useState(null)
  const [observacionesAbiertas, setObservacionesAbiertas] = useState(false)
  const [responsableCambio, setResponsableCambio] = useState(null)
  const [errorPublicacion, setErrorPublicacion] = useState('')
  const [publicadoAhora, setPublicadoAhora] = useState(false)
  const parametrosVisibles = useMemo(
    () => (data?.parametros ?? []).filter((item) => item.codigo !== 'unidad_reportada'),
    [data],
  )
  const values = useMemo(() => Object.fromEntries(parametrosVisibles.map((item) => [item.id, item.valor ?? ''])), [parametrosVisibles])
  const [cambios, setCambios] = useState({})
  const visibleValues = { ...values, ...cambios }
  const observacionesVisibles = observacionesCambio ?? data?.observaciones ?? ''
  const mostrarObservaciones = observacionesAbiertas || Boolean(observacionesVisibles.trim())
  const readOnly = data?.estado_resultado === 'publicado'
  const responsableVisible = responsableCambio ?? (readOnly
    ? data?.responsable_publicacion ?? data?.responsable_analisis ?? ''
    : data?.responsable_analisis ?? '')
  const cambiosSinGuardar = Object.keys(cambios).length > 0 || observacionesCambio !== null || responsableCambio !== null
  const esperandoMuestra = data?.estado_estudio === 'pendiente_muestra'
  const save = useMutation({
    mutationFn: () => guardarBorrador(estudioId, {
      observaciones: observacionesVisibles,
      responsable_analisis: responsableVisible.trim(),
      valores: parametrosVisibles.map((parametro) => ({ parametro_id: parametro.id, valor: visibleValues[parametro.id] || null })),
    }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudioId] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      setCambios({})
      setObservacionesCambio(null)
      setResponsableCambio(null)
    },
  })
  const publish = useMutation({
    mutationFn: () => publicarResultado(estudioId, responsableVisible.trim()),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudioId] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      await queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud'] })
      setPublicadoAhora(true)
    },
    onError: (error) => setErrorPublicacion(mensajeError(error)),
  })
  const busy = save.isPending || publish.isPending
  const grupos = parametrosVisibles.reduce((result, parametro) => {
    const nombre = parametro.seccion || 'Resultado'
    result[nombre] ??= []
    result[nombre].push(parametro)
    return result
  }, {})
  const Titulo = enArea ? 'h2' : 'h1'
  const tituloId = `lab-result-title-${estudioId}`

  return (
      <article className="lab-result-sheet" aria-labelledby={tituloId}>
        <header className="lab-result-sheet-header">
          {!enArea && <p className="lab-eyebrow">CAPTURA Y REVISIÓN</p>}<Titulo id={tituloId}>{data?.tipo_estudio_nombre || 'Resultado del estudio'}</Titulo>
          {data && <p>{data.referencia_estudio} · {data.paciente_nombre}</p>}
        </header>
        {isLoading && <div className="lab-result-sheet-body"><p>Cargando el formato de resultados…</p></div>}
        {isError && <div className="lab-result-sheet-body"><p className="lab-form-error" role="alert">No se pudo cargar el estudio. Vuelve a la solicitud e inténtalo de nuevo.</p></div>}
        {!isLoading && !isError && <>
          <div className="lab-result-sheet-body">
            {publicadoAhora && <p role="status" className="lab-result-status">Resultado publicado.</p>}
            {esperandoMuestra && <p className="lab-result-note">Primero registra la muestra de este estudio desde la solicitud.</p>}
            {!data.plantilla_configurada && <p className="lab-result-note">Este estudio todavía no tiene campos de resultado configurados.</p>}
            {data.plantilla_configurada && !esperandoMuestra && <>
              {Object.entries(grupos).map(([seccion, parametros]) => <section className="lab-result-group" key={seccion}>
                <h3>{seccion}</h3>
                <div className="lab-form-grid">
                  {parametros.map((parametro) => <label className="lab-result-field" key={parametro.id}>
                    {parametro.nombre}{parametro.obligatorio ? ' *' : ''}
                    {parametro.opciones?.length ? <select
                      value={visibleValues[parametro.id] ?? ''}
                      disabled={readOnly || busy}
                      onChange={(event) => setCambios((current) => ({ ...current, [parametro.id]: event.target.value }))}
                      aria-label={parametro.nombre}
                    ><option value="">Seleccionar resultado</option>{parametro.opciones.map((opcion) => <option key={opcion} value={opcion}>{opcion}</option>)}</select> : <input
                      type={parametro.tipo_entrada === 'decimal' || parametro.tipo_entrada === 'entero' ? 'number' : 'text'}
                      inputMode={parametro.tipo_entrada === 'decimal' || parametro.tipo_entrada === 'entero' ? 'decimal' : undefined}
                      step={parametro.tipo_entrada === 'decimal' ? 'any' : parametro.tipo_entrada === 'entero' ? '1' : undefined}
                      value={visibleValues[parametro.id] ?? ''}
                      disabled={readOnly || busy}
                      maxLength={2000}
                      onChange={(event) => setCambios((current) => ({ ...current, [parametro.id]: event.target.value }))}
                      aria-label={parametro.nombre}
                    />}
                    {(parametro.unidad || parametro.rango_referencia) && <small>{[parametro.unidad, parametro.rango_referencia].filter(Boolean).join(' · ')}</small>}
                  </label>)}
                </div>
              </section>)}
              <section className="lab-form-section">
                <label className="lab-observations-toggle">
                  <input type="checkbox" checked={mostrarObservaciones} onChange={(event) => {
                    setObservacionesAbiertas(event.target.checked)
                    if (!event.target.checked) setObservacionesCambio('')
                  }} disabled={readOnly || busy} />
                  Agregar observaciones
                </label>
                {mostrarObservaciones && <label className="lab-search-label">Observaciones generales
                  <textarea value={observacionesVisibles} onChange={(event) => setObservacionesCambio(event.target.value)} disabled={readOnly || busy} maxLength={4000} rows={3} />
                </label>}
                <label className="lab-search-label">Profesional responsable del resultado
                  <input required value={responsableVisible} onChange={(event) => setResponsableCambio(event.target.value)} disabled={readOnly || busy} maxLength={200} placeholder="Nombre y apellido" />
                </label>
                <p className="lab-form-hint">Los campos y referencias corresponden al formato de este estudio.</p>
                {cambiosSinGuardar && <p className="lab-form-hint" role="status">Guarda los cambios antes de publicar.</p>}
              </section>
            </>}
            {(save.isError || errorPublicacion) && <p className="lab-form-error" role="alert">{mensajeError(save.error || publish.error)}</p>}
          </div>
          <footer className="lab-result-sheet-footer">
            {data.plantilla_configurada && !readOnly && !esperandoMuestra && <>
              <button type="button" disabled={save.isPending || responsableVisible.trim().length < 2} onClick={() => save.mutate()}>{save.isPending ? 'Guardando…' : 'Guardar borrador'}</button>
              <button className="primary-button" type="button" disabled={publish.isPending || save.isPending || !data.estado_resultado || cambiosSinGuardar || responsableVisible.trim().length < 2} onClick={() => { setErrorPublicacion(''); publish.mutate() }}>{publish.isPending ? 'Publicando…' : 'Revisar y publicar'}</button>
            </>}
          </footer>
        </>}
      </article>
  )
}
