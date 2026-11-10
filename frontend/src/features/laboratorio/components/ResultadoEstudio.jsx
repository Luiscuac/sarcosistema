import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { guardarBorrador, obtenerExamen, publicarResultado } from '../api/laboratorioApi.js'
import CampoResultado from './resultados/CampoResultado.jsx'
import ConfirmarPublicacion from './resultados/ConfirmarPublicacion.jsx'
import ResumenCaptura from './resultados/ResumenCaptura.jsx'
import { useResponsableRecordado } from '../hooks/useResponsableRecordado.js'
import { agruparPorSeccion, enfocarSiguienteCampo, motivoPublicacionBloqueada, parametrosVisibles, resumenCaptura } from '../utils/captura.js'
import { mensajeError } from '../utils/mensajeError.js'
import { useAvisoCambiosSinGuardar } from '../../../shared/hooks/useAvisoCambiosSinGuardar.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import './resultados/ResultadoEstudio.css'

export default function ResultadoEstudio({ estudioId, usuario }) {
  const queryClient = useQueryClient()
  const { notificar } = useNotificacion()
  const { recordado, recordar } = useResponsableRecordado(usuario)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['resultado', estudioId],
    queryFn: () => obtenerExamen(estudioId),
  })
  // Solo se guardan los cambios del usuario; el resto viene del servidor.
  const [cambios, setCambios] = useState({})
  const [observacionesCambio, setObservacionesCambio] = useState(null)
  const [observacionesAbiertas, setObservacionesAbiertas] = useState(false)
  const [responsableCambio, setResponsableCambio] = useState(null)
  const [confirmando, setConfirmando] = useState(false)

  const parametros = useMemo(() => parametrosVisibles(data?.parametros), [data])
  const valores = { ...Object.fromEntries(parametros.map((parametro) => [parametro.id, parametro.valor ?? ''])), ...cambios }
  const soloLectura = data?.estado_resultado === 'publicado'
  const esperandoMuestra = data?.estado_estudio === 'pendiente_muestra'
  const observaciones = observacionesCambio ?? data?.observaciones ?? ''
  const mostrarObservaciones = observacionesAbiertas || Boolean(observaciones.trim())
  const responsable = responsableCambio ?? (soloLectura
    ? data?.responsable_publicacion ?? data?.responsable_analisis ?? ''
    : data?.responsable_analisis || recordado)
  const cambiosEnCaptura = Object.keys(cambios).length > 0 || observacionesCambio !== null
  const hayCambios = cambiosEnCaptura || responsable.trim() !== (data?.responsable_analisis ?? '')
  const resumen = resumenCaptura(parametros, valores)
  const motivoBloqueo = motivoPublicacionBloqueada({
    hayCambios, responsable, faltantes: resumen.faltantes, sinBorrador: !data?.estado_resultado,
  })
  useAvisoCambiosSinGuardar(cambiosEnCaptura && !soloLectura)

  const guardar = useMutation({
    mutationFn: () => guardarBorrador(estudioId, {
      observaciones,
      responsable_analisis: responsable.trim(),
      valores: parametros.map((parametro) => ({ parametro_id: parametro.id, valor: String(valores[parametro.id] ?? '').trim() || null })),
    }),
    onSuccess: async () => {
      recordar(responsable)
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudioId] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      setCambios({})
      setObservacionesCambio(null)
      setResponsableCambio(null)
      notificar('Borrador guardado.', 'exito')
    },
    onError: (error) => notificar(mensajeError(error, 'No se pudo guardar el resultado.'), 'error'),
  })
  const publicar = useMutation({
    mutationFn: () => publicarResultado(estudioId, responsable.trim()),
    onSuccess: async () => {
      setConfirmando(false)
      await queryClient.invalidateQueries({ queryKey: ['resultado', estudioId] })
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      await queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud'] })
      notificar('Resultado publicado. El médico ya puede consultarlo.', 'exito')
    },
    onError: (error) => {
      setConfirmando(false)
      notificar(mensajeError(error, 'No se pudo publicar el resultado.'), 'error')
    },
  })
  const ocupado = guardar.isPending || publicar.isPending
  const editable = data?.plantilla_configurada && !soloLectura && !esperandoMuestra

  return (
    <article className="lab-result-sheet" aria-labelledby={`lab-result-title-${estudioId}`}>
      <header className="lab-result-sheet-header">
        <p className="lab-eyebrow">CAPTURA Y REVISIÓN</p>
        <h1 id={`lab-result-title-${estudioId}`}>{data?.tipo_estudio_nombre || 'Resultado del estudio'}</h1>
        {data && <p>{data.referencia_estudio} · {data.paciente_nombre}</p>}
      </header>
      {isLoading && <div className="lab-result-sheet-body"><p>Cargando el formato de resultados…</p></div>}
      {isError && <div className="lab-result-sheet-body"><p className="lab-form-error" role="alert">No se pudo cargar el estudio. Vuelve a la solicitud e inténtalo de nuevo.</p></div>}
      {data && <form onKeyDown={enfocarSiguienteCampo} onSubmit={(evento) => { evento.preventDefault(); guardar.mutate() }}>
        <div className="lab-result-sheet-body">
          {soloLectura && <p role="status" className="lab-result-status">Resultado publicado. Se muestra en modo lectura.</p>}
          {esperandoMuestra && <p className="lab-result-note">Primero registra la muestra de este estudio desde la solicitud.</p>}
          {!data.plantilla_configurada && <p className="lab-result-note">Este estudio todavía no tiene campos de resultado configurados.</p>}
          {editable && <ResumenCaptura resumen={resumen} motivoBloqueo={motivoBloqueo} />}
          {data.plantilla_configurada && !esperandoMuestra && <>
            {agruparPorSeccion(parametros).map(([seccion, grupo]) => <section className="lab-result-group" key={seccion}>
              <h3>{seccion}</h3>
              <div className="lab-form-grid">
                {grupo.map((parametro) => <CampoResultado key={parametro.id} parametro={parametro} valor={valores[parametro.id]}
                  deshabilitado={soloLectura || ocupado}
                  onCambiar={(valor) => setCambios((actual) => ({ ...actual, [parametro.id]: valor }))} />)}
              </div>
            </section>)}
            <section className="lab-form-section">
              <label className="lab-observations-toggle">
                <input type="checkbox" checked={mostrarObservaciones} disabled={soloLectura || ocupado} onChange={(evento) => {
                  setObservacionesAbiertas(evento.target.checked)
                  if (!evento.target.checked) setObservacionesCambio('')
                }} />
                Agregar observaciones
              </label>
              {mostrarObservaciones && <label className="lab-search-label">Observaciones generales
                <textarea value={observaciones} onChange={(evento) => setObservacionesCambio(evento.target.value)} disabled={soloLectura || ocupado} maxLength={4000} rows={3} />
              </label>}
              <label className="lab-search-label">Profesional responsable del resultado
                <input required value={responsable} onChange={(evento) => setResponsableCambio(evento.target.value)} disabled={soloLectura || ocupado} maxLength={200} placeholder="Nombre y apellido" />
              </label>
            </section>
          </>}
        </div>
        {editable && <footer className="lab-result-sheet-footer">
          <button type="submit" disabled={ocupado || responsable.trim().length < 2 || !hayCambios}>{guardar.isPending ? 'Guardando…' : 'Guardar borrador'}</button>
          <button className="primary-button" type="button" disabled={ocupado || Boolean(motivoBloqueo)} title={motivoBloqueo ?? undefined}
            onClick={() => setConfirmando(true)}>Revisar y publicar</button>
        </footer>}
      </form>}
      {confirmando && <ConfirmarPublicacion estudios={[{ ...data, parametros }]} valores={valores} responsable={responsable.trim()}
        resumen={resumen} pendiente={publicar.isPending} onConfirmar={() => publicar.mutate()} onCancelar={() => setConfirmando(false)} />}
    </article>
  )
}
