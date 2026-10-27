import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { buscarPacientes, crearPaciente, crearSolicitud, listarEstudiosCatalogo } from '../api/laboratorioApi.js'
import DatosPedido from './nueva-solicitud/DatosPedido.jsx'
import EstudiosSolicitados from './nueva-solicitud/EstudiosSolicitados.jsx'
import PacienteSolicitud from './nueva-solicitud/PacienteSolicitud.jsx'
import './nueva-solicitud/NuevaSolicitud.css'

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
            <PacienteSolicitud
              paciente={paciente} nuevoPaciente={nuevoPaciente} datosPaciente={datosPaciente}
              termino={termino} pacientesQuery={pacientesQuery} crearPacientePendiente={crearPacienteMutation.isPending}
              onSelect={(seleccionado) => { setPaciente(seleccionado); setErrorLocal('') }}
              onTerminoChange={setTermino} onStartCreate={() => setNuevoPaciente(true)}
              onCancelCreate={() => setNuevoPaciente(false)} onPacienteChange={cambiarPaciente}
              onCreatePaciente={crearPacienteAhora}
            />
            <DatosPedido datos={datosSolicitud} onChange={cambiarSolicitud} />
            <EstudiosSolicitados
              cargando={catalogoQuery.isLoading} error={catalogoQuery.isError} catalogo={catalogoQuery.data ?? []}
              busqueda={busquedaEstudio} onBusquedaChange={setBusquedaEstudio}
              cantidadSeleccionada={estudioIds.length} idsSeleccionados={estudioIds}
              grupos={gruposVisibles} estudiosVisibles={estudiosVisibles} onToggle={alternarEstudio}
            />
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
