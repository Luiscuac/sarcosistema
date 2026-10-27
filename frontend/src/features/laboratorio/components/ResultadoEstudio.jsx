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
    return `El backend respondió con un error HTTP ${error.response.status}. Revisa la terminal de Uvicorn para ver el detalle.`
  }
  if (error.request) {
    return 'No se recibió respuesta del backend. Comprueba que Uvicorn siga ejecutándose y vuelve a intentar.'
  }
  return error.message || 'No se pudo guardar el resultado.'
}

export default function ResultadoEstudio({ estudio, onClose }) {
  const queryClient = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['resultado', estudio.estudio_id],
    queryFn: () => obtenerExamen(estudio.estudio_id),
  })
  const [observacionesCambio, setObservacionesCambio] = useState(null)
  const [errorPublicacion, setErrorPublicacion] = useState('')
  const values = useMemo(() => Object.fromEntries((data?.parametros ?? []).map((item) => [item.id, item.valor ?? ''])), [data])
  const [cambios, setCambios] = useState({})
  const visibleValues = { ...values, ...cambios }
  const observacionesVisibles = observacionesCambio ?? data?.observaciones ?? ''
  const cambiosSinGuardar = Object.keys(cambios).length > 0 || observacionesCambio !== null
  const readOnly = data?.estado_resultado === 'publicado'
  const save = useMutation({
    mutationFn: () => guardarBorrador(estudio.estudio_id, {
      observaciones: observacionesVisibles,
      valores: (data?.parametros ?? []).map((parametro) => ({ parametro_id: parametro.id, valor: visibleValues[parametro.id] || null })),
    }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudio.estudio_id] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      setCambios({})
      setObservacionesCambio(null)
    },
  })
  const publish = useMutation({
    mutationFn: () => publicarResultado(estudio.estudio_id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudio.estudio_id] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      onClose()
    },
    onError: (error) => setErrorPublicacion(mensajeError(error)),
  })
  const busy = save.isPending || publish.isPending
  const grupos = (data?.parametros ?? []).reduce((result, parametro) => {
    const nombre = parametro.seccion || 'Resultado'
    result[nombre] ??= []
    result[nombre].push(parametro)
    return result
  }, {})

  return (
    <div className="lab-dialog-backdrop" role="presentation" onMouseDown={(event) => { if (!busy && event.target === event.currentTarget) onClose() }}>
      <section className="lab-dialog" role="dialog" aria-modal="true" aria-labelledby="lab-result-title">
        <header className="lab-dialog-header">
          <div><p className="lab-eyebrow">CAPTURA Y REVISIÓN</p><h2 id="lab-result-title">{data?.tipo_estudio_nombre || estudio.tipo_estudio_nombre}</h2>
            <p>{data?.referencia_estudio || estudio.referencia_estudio} · {data?.paciente_nombre || estudio.paciente_nombre}</p></div>
          <button className="lab-dialog-close" type="button" onClick={onClose} disabled={busy} aria-label="Cerrar">×</button>
        </header>
        {isLoading && <div className="lab-dialog-body"><p className="lab-form-section">Cargando el formato de resultados…</p></div>}
        {isError && <div className="lab-dialog-body"><p className="lab-form-error" role="alert">No se pudo abrir el resultado. Cierra esta ventana e inténtalo de nuevo.</p></div>}
        {!isLoading && !isError && <>
          <div className="lab-dialog-body">
            {!data.plantilla_configurada && <p className="lab-result-note">No hay campos de resultado disponibles para este estudio. Contacta al responsable del catálogo de laboratorio.</p>}
            {data.plantilla_configurada && <>
              {data.estado_resultado && <p className="lab-result-status">Estado: {data.estado_resultado === 'publicado' ? `Publicado · versión ${data.numero_version}` : `Borrador · versión ${data.numero_version}`}</p>}
              {Object.entries(grupos).map(([seccion, parametros]) => <section className="lab-result-group" key={seccion}>
                <h3>{seccion}</h3>
                <div className="lab-form-grid">
                  {parametros.map((parametro) => <label className="lab-result-field" key={parametro.id}>
                    {parametro.nombre}{parametro.obligatorio ? ' *' : ''}
                    <input
                      type={parametro.tipo_entrada === 'decimal' ? 'number' : 'text'}
                      inputMode={parametro.tipo_entrada === 'decimal' || parametro.tipo_entrada === 'entero' ? 'decimal' : undefined}
                      step={parametro.tipo_entrada === 'decimal' ? 'any' : undefined}
                      value={visibleValues[parametro.id] ?? ''}
                      disabled={readOnly || busy}
                      maxLength={2000}
                      onChange={(event) => setCambios((current) => ({ ...current, [parametro.id]: event.target.value }))}
                      aria-label={parametro.nombre}
                    />
                    {(parametro.unidad || parametro.rango_referencia) && <small>{[parametro.unidad, parametro.rango_referencia].filter(Boolean).join(' · ')}</small>}
                  </label>)}
                </div>
              </section>)}
              <section className="lab-form-section">
                <label className="lab-search-label">Observaciones generales
                  <textarea value={observacionesVisibles} onChange={(event) => setObservacionesCambio(event.target.value)} disabled={readOnly || busy} maxLength={4000} rows={3} />
                </label>
                <p className="lab-form-hint">Los campos y referencias se muestran desde la versión activa del formato del estudio.</p>
                {cambiosSinGuardar && <p className="lab-form-hint" role="status">Guarda los cambios antes de publicar.</p>}
              </section>
            </>}
            {(save.isError || errorPublicacion) && <p className="lab-form-error" role="alert">{mensajeError(save.error || publish.error)}</p>}
          </div>
          <footer className="lab-dialog-footer">
            <button type="button" onClick={onClose} disabled={busy}>Cerrar</button>
            {data.plantilla_configurada && !readOnly && <>
              <button type="button" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending ? 'Guardando…' : 'Guardar borrador'}</button>
              <button className="primary-button" type="button" disabled={publish.isPending || save.isPending || !data.estado_resultado || cambiosSinGuardar} onClick={() => { setErrorPublicacion(''); publish.mutate() }}>{publish.isPending ? 'Publicando…' : 'Revisar y publicar'}</button>
            </>}
          </footer>
        </>}
      </section>
    </div>
  )
}
