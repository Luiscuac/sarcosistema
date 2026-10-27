import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { buscarPacientes, crearPaciente, crearSolicitud, listarEstudiosCatalogo } from '../api/laboratorioApi.js'
import './NuevaSolicitud.css'

const pacienteVacio = {
  nombre_completo: '',
  fecha_nacimiento: '',
  sexo: 'no_especificado',
  tipo_documento: 'CI',
  numero_documento: '',
  sin_documento: false,
  historia_clinica: '',
  codigo_externo: '',
}

const gruposEstudios = [
  { codigo: 'hematologia', nombre: 'Hematología' },
  { codigo: 'bioquimica', nombre: 'Bioquímica' },
  { codigo: 'serologia', nombre: 'Serología' },
  { codigo: 'copro_orina', nombre: 'Copro y orina' },
]

function mensajeDeError(error, mensajePredeterminado) {
  const detalle = error.response?.data?.detail
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle.map((item) => item?.msg).filter(Boolean).join(' · ') || mensajePredeterminado
  }
  return mensajePredeterminado
}

export default function NuevaSolicitud({ onClose, onCreated }) {
  const queryClient = useQueryClient()
  const claveIdempotencia = useRef(crypto.randomUUID())
  const [termino, setTermino] = useState('')
  const [paciente, setPaciente] = useState(null)
  const [nuevoPaciente, setNuevoPaciente] = useState(false)
  const [datosPaciente, setDatosPaciente] = useState(pacienteVacio)
  const [estudioIds, setEstudioIds] = useState([])
  const [busquedaEstudio, setBusquedaEstudio] = useState('')
  const [datosSolicitud, setDatosSolicitud] = useState({
    referencia_papel_formulario: '',
    establecimiento_solicitante_nombre: '',
    medico_solicitante_nombre: '',
    diagnostico_principal: '',
    prioridad: 'sin_prioridad',
  })
  const [errorLocal, setErrorLocal] = useState('')

  const catalogoQuery = useQuery({
    queryKey: ['laboratorio', 'catalogo-estudios'],
    queryFn: listarEstudiosCatalogo,
  })
  const pacientesQuery = useQuery({
    queryKey: ['laboratorio', 'pacientes', termino],
    queryFn: () => buscarPacientes(termino.trim()),
    enabled: termino.trim().length >= 2 && !nuevoPaciente,
  })
  const crearPacienteMutation = useMutation({
    mutationFn: crearPaciente,
    onSuccess: (nuevo) => {
      setPaciente(nuevo)
      setNuevoPaciente(false)
      setTermino('')
      setErrorLocal('')
      queryClient.invalidateQueries({ queryKey: ['laboratorio', 'pacientes'] })
    },
    onError: (error) => setErrorLocal(mensajeDeError(error, 'No se pudo registrar el paciente. Comprueba los datos e inténtalo nuevamente.')),
  })
  const crearSolicitudMutation = useMutation({
    mutationFn: crearSolicitud,
    onSuccess: async (solicitud) => {
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      await queryClient.invalidateQueries({ queryKey: ['laboratorio'] })
      onCreated?.(solicitud)
      onClose()
    },
    onError: (error) => setErrorLocal(mensajeDeError(error, 'No se pudo registrar la solicitud.')),
  })

  const cambiarSolicitud = (campo, valor) => setDatosSolicitud((actual) => ({ ...actual, [campo]: valor }))
  const cambiarPaciente = (campo, valor) => setDatosPaciente((actual) => {
    if (campo === 'sin_documento' && valor) {
      return { ...actual, sin_documento: true, tipo_documento: '', numero_documento: '' }
    }
    return { ...actual, [campo]: valor }
  })
  const alternarEstudio = (id) => setEstudioIds((actual) =>
    actual.includes(id) ? actual.filter((item) => item !== id) : [...actual, id],
  )

  const enviar = (event) => {
    event.preventDefault()
    setErrorLocal('')
    if (!paciente) {
      setErrorLocal('Busca y selecciona un paciente antes de continuar.')
      return
    }
    if (!estudioIds.length) {
      setErrorLocal('Selecciona al menos un estudio.')
      return
    }
    crearSolicitudMutation.mutate({
      ...datosSolicitud,
      paciente_id: paciente.id,
      tipo_estudio_ids: estudioIds,
      clave_idempotencia: claveIdempotencia.current,
    })
  }

  const crearPacienteAhora = (event) => {
    event.preventDefault()
    setErrorLocal('')
    const nombre = datosPaciente.nombre_completo.trim()
    if (nombre.length < 2) {
      setErrorLocal('Escribe el nombre completo del paciente.')
      return
    }
    if (!datosPaciente.fecha_nacimiento) {
      setErrorLocal('Selecciona la fecha de nacimiento del paciente.')
      return
    }
    if (!datosPaciente.sin_documento
        && (!datosPaciente.tipo_documento.trim() || !datosPaciente.numero_documento.trim())) {
      setErrorLocal('Ingresa el documento o marca “Persona sin documento”.')
      return
    }
    crearPacienteMutation.mutate({
      ...datosPaciente,
      nombre_completo: nombre,
      tipo_documento: datosPaciente.sin_documento ? null : datosPaciente.tipo_documento.trim(),
      numero_documento: datosPaciente.sin_documento ? null : datosPaciente.numero_documento.trim(),
      historia_clinica: datosPaciente.historia_clinica.trim() || null,
      codigo_externo: datosPaciente.codigo_externo.trim() || null,
    })
  }

  const terminoEstudio = busquedaEstudio.trim().toLocaleLowerCase()
  const estudiosVisibles = (catalogoQuery.data ?? []).filter((item) =>
    item.nombre.toLocaleLowerCase().includes(terminoEstudio))
  const gruposVisibles = [
    ...gruposEstudios,
    { codigo: null, nombre: 'Prestaciones por clasificar' },
  ].map((grupo) => ({
    ...grupo,
    estudios: estudiosVisibles.filter((item) => item.categoria_laboratorio === grupo.codigo),
  })).filter((grupo) => grupo.estudios.length > 0)

  return (
    <div className="lab-dialog-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="lab-dialog" role="dialog" aria-modal="true" aria-labelledby="new-request-title">
        <header className="lab-dialog-header">
          <div>
            <span className="lab-eyebrow">D-8 · SOLICITUD DE EXÁMENES</span>
            <h2 id="new-request-title">Nueva solicitud</h2>
            <p>Identifica al paciente y registra los estudios que llegaron en el pedido.</p>
          </div>
          <button className="lab-dialog-close" type="button" onClick={onClose} aria-label="Cerrar">×</button>
        </header>

        <form onSubmit={enviar}>
          <div className="lab-dialog-body">
            <section className="lab-form-section">
              <h3>1. Paciente</h3>
              {paciente ? (
                <div className="lab-selected-patient">
                  <div><strong>{paciente.nombre_completo}</strong><span>{paciente.codigo_paciente} · {paciente.numero_documento || 'Sin documento'}{paciente.historia_clinica ? ` · HC ${paciente.historia_clinica}` : ''}</span></div>
                  <button type="button" onClick={() => setPaciente(null)}>Cambiar</button>
                </div>
              ) : nuevoPaciente ? (
                <div className="lab-inline-patient-form">
                  <div className="lab-form-grid">
                    <label>Nombre completo<input required minLength="2" value={datosPaciente.nombre_completo} onChange={(e) => cambiarPaciente('nombre_completo', e.target.value)} /></label>
                    <label>Fecha de nacimiento<input required type="date" value={datosPaciente.fecha_nacimiento} onChange={(e) => cambiarPaciente('fecha_nacimiento', e.target.value)} /></label>
                    <label>Sexo registrado<select value={datosPaciente.sexo} onChange={(e) => cambiarPaciente('sexo', e.target.value)}><option value="no_especificado">No especificado</option><option value="F">F</option><option value="M">M</option><option value="otro">Otro</option></select></label>
                    <label>N.º de historia clínica<input value={datosPaciente.historia_clinica} onChange={(e) => cambiarPaciente('historia_clinica', e.target.value)} placeholder="Si figura en el registro" maxLength="80" /></label>
                    <label>Código externo del hospital<input value={datosPaciente.codigo_externo} onChange={(e) => cambiarPaciente('codigo_externo', e.target.value)} placeholder="Si figura en el registro" maxLength="80" /></label>
                    <label className="lab-checkbox-label"><input type="checkbox" checked={datosPaciente.sin_documento} onChange={(e) => cambiarPaciente('sin_documento', e.target.checked)} /> Persona sin documento</label>
                    {!datosPaciente.sin_documento && <>
                      <label>Tipo de documento<input required value={datosPaciente.tipo_documento} onChange={(e) => cambiarPaciente('tipo_documento', e.target.value)} /></label>
                      <label>Número de documento<input required value={datosPaciente.numero_documento} onChange={(e) => cambiarPaciente('numero_documento', e.target.value)} /></label>
                    </>}
                  </div>
                  <div className="lab-inline-actions">
                    <button type="button" onClick={() => setNuevoPaciente(false)}>Cancelar</button>
                    <button className="primary-button" type="button" disabled={crearPacienteMutation.isPending} onClick={crearPacienteAhora}>
                      {crearPacienteMutation.isPending ? 'Guardando…' : 'Guardar paciente'}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <label className="lab-search-label">Buscar por nombre, documento, historia clínica o código
                    <input autoFocus type="search" value={termino} onChange={(e) => setTermino(e.target.value)} placeholder="Escribe al menos 2 caracteres" />
                  </label>
                  {pacientesQuery.isLoading && <p className="lab-form-hint">Buscando pacientes…</p>}
                  {pacientesQuery.isError && <p className="lab-form-error">No se pudo buscar. Comprueba la conexión e inténtalo de nuevo.</p>}
                  {(pacientesQuery.data ?? []).map((item) => (
                    <button className="lab-patient-option" type="button" key={item.id} onClick={() => { setPaciente(item); setErrorLocal('') }}>
                      <strong>{item.nombre_completo}</strong><span>{item.codigo_paciente} · {item.numero_documento || 'Sin documento'} · {item.fecha_nacimiento}{item.historia_clinica ? ` · HC ${item.historia_clinica}` : ''}{item.codigo_externo ? ` · Código ${item.codigo_externo}` : ''}</span>
                    </button>
                  ))}
                  {termino.trim().length >= 2 && pacientesQuery.data?.length === 0 && <p className="lab-form-hint">No se encontró el paciente. Puedes registrar una identificación mínima.</p>}
                  <button className="lab-text-button" type="button" onClick={() => setNuevoPaciente(true)}>Registrar paciente si no existe</button>
                </>
              )}
            </section>

            <section className="lab-form-section">
              <h3>2. Datos del pedido</h3>
              <div className="lab-form-grid">
                <label>Referencia del formulario<input value={datosSolicitud.referencia_papel_formulario} onChange={(e) => cambiarSolicitud('referencia_papel_formulario', e.target.value)} placeholder="Opcional" /></label>
                <label>Establecimiento solicitante<input value={datosSolicitud.establecimiento_solicitante_nombre} onChange={(e) => cambiarSolicitud('establecimiento_solicitante_nombre', e.target.value)} placeholder="Según D-8" /></label>
                <label>Profesional solicitante<input required value={datosSolicitud.medico_solicitante_nombre} onChange={(e) => cambiarSolicitud('medico_solicitante_nombre', e.target.value)} /></label>
                <label>Prioridad<select value={datosSolicitud.prioridad} onChange={(e) => cambiarSolicitud('prioridad', e.target.value)}><option value="sin_prioridad">Programada / sin prioridad</option><option value="urgente">Urgente</option></select></label>
                <label className="lab-full-field">Diagnóstico principal<input value={datosSolicitud.diagnostico_principal} onChange={(e) => cambiarSolicitud('diagnostico_principal', e.target.value)} placeholder="Opcional" /></label>
              </div>
            </section>

            <section className="lab-form-section">
              <h3>3. Estudios solicitados</h3>
              {catalogoQuery.isLoading && <p className="lab-form-hint">Cargando catálogo…</p>}
              {catalogoQuery.isError && <p className="lab-form-error">No se pudo cargar el catálogo de laboratorio.</p>}
              {!catalogoQuery.isLoading && !catalogoQuery.isError && !(catalogoQuery.data ?? []).length && (
                <p className="lab-form-hint">No hay estudios disponibles para registrar. Contacta al administrador del sistema.</p>
              )}
              <p className="lab-form-hint">Selecciona las pruebas indicadas en el pedido. Cada una quedará asociada a esta solicitud.</p>
              <label className="lab-search-label lab-study-search">Buscar estudio
                <input type="search" value={busquedaEstudio} onChange={(event) => setBusquedaEstudio(event.target.value)} placeholder="Nombre de la prueba" />
              </label>
              <p className="lab-form-hint" role="status">{estudioIds.length} {estudioIds.length === 1 ? 'estudio seleccionado' : 'estudios seleccionados'}</p>
              {gruposVisibles.map((grupo) => <div className="lab-study-group" key={grupo.codigo ?? 'sin-categoria'}>
                  <h4>{grupo.nombre}</h4>
                  <div className="lab-study-options">
                    {grupo.estudios.map((estudio) => (
                      <label className="lab-study-option" key={estudio.id}>
                        <input type="checkbox" checked={estudioIds.includes(estudio.id)} onChange={() => alternarEstudio(estudio.id)} />
                        <span><strong>{estudio.nombre}</strong></span>
                      </label>
                    ))}
                  </div>
                </div>)}
              {terminoEstudio && !estudiosVisibles.length &&
                <p className="lab-form-hint">No hay estudios con ese nombre.</p>}
            </section>
            {errorLocal && <p className="lab-form-error" role="alert">{errorLocal}</p>}
          </div>
          <footer className="lab-dialog-footer">
            <button type="button" onClick={onClose}>Cancelar</button>
            <button className="primary-button" type="submit" disabled={crearSolicitudMutation.isPending || !catalogoQuery.data?.length}>
              {crearSolicitudMutation.isPending ? 'Registrando…' : 'Registrar solicitud'}
            </button>
          </footer>
        </form>
      </section>
    </div>
  )
}
