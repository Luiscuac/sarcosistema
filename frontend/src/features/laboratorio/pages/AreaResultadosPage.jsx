import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { guardarBorradorArea, obtenerExamen, obtenerSolicitud, publicarResultadosArea } from '../api/laboratorioApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NavegacionLab from '../components/NavegacionLab.jsx'
import CampoResultado from '../components/resultados/CampoResultado.jsx'
import ConfirmarPublicacion from '../components/resultados/ConfirmarPublicacion.jsx'
import ResumenCaptura from '../components/resultados/ResumenCaptura.jsx'
import { useResponsableRecordado } from '../hooks/useResponsableRecordado.js'
import { agruparPorCategoria } from '../utils/agruparSolicitudes.js'
import { agruparPorSeccion, enfocarSiguienteCampo, motivoPublicacionBloqueada, parametrosVisibles, resumenCaptura } from '../utils/captura.js'
import { mensajeError } from '../utils/mensajeError.js'
import { useAvisoCambiosSinGuardar } from '../../../shared/hooks/useAvisoCambiosSinGuardar.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import './laboratorio.css'
import './area-resultados.css'

const SIN_RESULTADOS = []

export default function AreaResultadosPage({ usuario, logout }) {
  const { solicitudId, areaCodigo } = useParams()
  const queryClient = useQueryClient()
  const { notificar } = useNotificacion()
  const { recordado, recordar } = useResponsableRecordado(usuario)
  const [valores, setValores] = useState({})
  const [observaciones, setObservaciones] = useState('')
  const [observacionesActivas, setObservacionesActivas] = useState(false)
  const [responsable, setResponsable] = useState('')
  const [confirmando, setConfirmando] = useState(false)

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
    queryFn: () => Promise.all(listos.map((estudio) => obtenerExamen(estudio.estudio_id))),
    enabled: listos.length > 0,
  })
  const resultados = estudiosQuery.data ?? SIN_RESULTADOS
  const editables = resultados.filter((resultado) => resultado.estado_resultado !== 'publicado')
  const todoPublicado = resultados.length > 0 && editables.length === 0
  const guardado = resultados[0]

  useEffect(() => {
    if (!guardado) return
    setValores(Object.fromEntries(resultados.flatMap((resultado) => resultado.parametros.map((parametro) => [parametro.id, parametro.valor ?? '']))))
    setObservaciones(guardado.observaciones ?? '')
    setObservacionesActivas(Boolean(guardado.observaciones?.trim()))
    setResponsable(guardado.responsable_analisis ?? guardado.responsable_publicacion ?? recordado)
  }, [resultados, guardado, recordado])

  const parametrosEditables = editables.flatMap((resultado) => parametrosVisibles(resultado.parametros))
  const resumen = resumenCaptura(parametrosEditables, valores)
  const cambiosEnCaptura = resultados.some((resultado) => resultado.parametros.some((parametro) =>
    (valores[parametro.id] ?? '') !== (parametro.valor ?? '')))
    || (observacionesActivas ? observaciones : '') !== (guardado?.observaciones ?? '')
  const hayCambios = cambiosEnCaptura || responsable.trim() !== (guardado?.responsable_analisis ?? '')
  const motivoBloqueo = todoPublicado ? null : motivoPublicacionBloqueada({
    hayCambios,
    responsable,
    faltantes: resumen.faltantes,
    sinBorrador: editables.some((resultado) => resultado.estado_resultado !== 'borrador'),
  })
  useAvisoCambiosSinGuardar(cambiosEnCaptura && !todoPublicado)

  const refrescar = (incluirBandeja = false) => Promise.all([
    queryClient.invalidateQueries({ queryKey: ['laboratorio', 'area-resultados', solicitudId, areaCodigo] }),
    queryClient.invalidateQueries({ queryKey: ['resultado'] }),
    queryClient.invalidateQueries({ queryKey: ['laboratorio', 'solicitud', solicitudId] }),
    incluirBandeja && queryClient.invalidateQueries({ queryKey: ['examenes'] }),
  ])

  const guardar = useMutation({
    mutationFn: () => guardarBorradorArea(solicitudId, areaCodigo, {
      estudios: editables.map((resultado) => ({
        estudio_id: resultado.estudio_id,
        valores: parametrosVisibles(resultado.parametros).map((parametro) => ({
          parametro_id: parametro.id,
          valor: String(valores[parametro.id] ?? '').trim() || null,
        })),
      })),
      observaciones: observacionesActivas ? observaciones : '',
      responsable: responsable.trim(),
    }),
    onSuccess: async () => {
      recordar(responsable)
      await refrescar()
      notificar('Borrador guardado. Revisa los valores y publica cuando estén completos.', 'exito')
    },
    onError: async (error) => {
      notificar(mensajeError(error, 'No se pudo guardar el borrador del área.'), 'error')
      await refrescar()
    },
  })

  const publicar = useMutation({
    mutationFn: () => publicarResultadosArea(solicitudId, areaCodigo, {
      estudio_ids: editables.map((resultado) => resultado.estudio_id),
      responsable: responsable.trim(),
    }),
    onSuccess: async () => {
      setConfirmando(false)
      await refrescar(true)
      notificar('Resultados publicados. El médico ya puede consultarlos.', 'exito')
    },
    onError: async (error) => {
      setConfirmando(false)
      notificar(mensajeError(error, 'No se pudieron publicar los resultados del área.'), 'error')
      await refrescar()
    },
  })

  const ocupado = guardar.isPending || publicar.isPending
  const bloqueado = todoPublicado || ocupado
  const cambiarValor = (id) => (valor) => setValores((actual) => ({ ...actual, [id]: valor }))

  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-area-results-page">
        <NavegacionLab volverA={`/laboratorio/solicitudes/${solicitudId}`} textoVolver="Volver a la solicitud" migas={[
          { texto: 'Solicitudes', ruta: '/laboratorio' },
          { texto: solicitud?.referencia ?? 'Solicitud', ruta: `/laboratorio/solicitudes/${solicitudId}` },
          { texto: area?.nombre ?? 'Resultados' },
        ]} />
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
            <p>Registra la muestra desde la solicitud antes de capturar: {pendientes.map((estudio) => estudio.tipo_estudio_nombre).join(', ')}.</p>
          </div>}
          {noRealizados.length > 0 && <div className="lab-area-pending">
            <strong>Estudios no realizados</strong>
            <p>{noRealizados.map((estudio) => estudio.tipo_estudio_nombre).join(', ')}. La justificación registrada se incluirá en el informe final.</p>
          </div>}
          {estudiosQuery.isLoading && <p>Cargando formatos de resultados…</p>}
          {estudiosQuery.isError && <p role="alert">No se pudieron cargar los formatos de resultados.</p>}
          {todoPublicado && <p className="lab-area-published" role="status">Todos los resultados de esta área están publicados. Se muestran en modo lectura.</p>}
          {resultados.length > 0 && <form className="lab-area-result-form" onKeyDown={enfocarSiguienteCampo}
            onSubmit={(evento) => { evento.preventDefault(); guardar.mutate() }}>
            {!todoPublicado && <ResumenCaptura resumen={resumen} motivoBloqueo={motivoBloqueo} />}
            {resultados.map((resultado) => <section className="lab-area-study" key={resultado.estudio_id}>
              <header>
                <h2>{resultado.tipo_estudio_nombre}</h2>
                <small>{resultado.estado_resultado === 'publicado' ? 'Publicado · ' : ''}{resultado.referencia_estudio}</small>
              </header>
              {agruparPorSeccion(parametrosVisibles(resultado.parametros)).map(([seccion, parametros]) => <section className="lab-area-parameter-section" key={seccion}>
                <h3>{seccion}</h3>
                <div className="lab-form-grid">
                  {parametros.map((parametro) => <CampoResultado key={parametro.id} parametro={parametro} valor={valores[parametro.id]}
                    onCambiar={cambiarValor(parametro.id)} deshabilitado={bloqueado || resultado.estado_resultado === 'publicado'} />)}
                </div>
              </section>)}
            </section>)}
            <div className="lab-area-meta-fields">
              <label className="lab-search-label">Profesional responsable del área
                <input required minLength={2} maxLength={200} value={responsable} onChange={(evento) => setResponsable(evento.target.value)} disabled={bloqueado} placeholder="Nombre y apellido" />
              </label>
              <div className="lab-area-observations">
                <label className="lab-area-observations-toggle"><input type="checkbox" checked={observacionesActivas} onChange={(evento) => setObservacionesActivas(evento.target.checked)} disabled={bloqueado} /> Agregar observaciones</label>
                {observacionesActivas && <label className="lab-search-label">Observaciones generales del área
                  <textarea value={observaciones} onChange={(evento) => setObservaciones(evento.target.value)} disabled={bloqueado} maxLength={4000} rows={3} />
                </label>}
              </div>
            </div>
            {!todoPublicado && <footer className="lab-area-result-actions">
              <span className="lab-form-hint">Consejo: pulsa Enter para pasar al siguiente campo.</span>
              <button type="submit" disabled={ocupado || responsable.trim().length < 2 || !hayCambios}>{guardar.isPending ? 'Guardando…' : 'Guardar borrador'}</button>
              <button className="primary-button" type="button" disabled={ocupado || Boolean(motivoBloqueo)} title={motivoBloqueo ?? undefined}
                onClick={() => setConfirmando(true)}>Revisar y publicar</button>
            </footer>}
          </form>}
        </>}
      </section>
    </div>
    {confirmando && <ConfirmarPublicacion estudios={editables} valores={valores} responsable={responsable.trim()} resumen={resumen}
      pendiente={publicar.isPending} onConfirmar={() => publicar.mutate()} onCancelar={() => setConfirmando(false)} />}
  </main>
}
