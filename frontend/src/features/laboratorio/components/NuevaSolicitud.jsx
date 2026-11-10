import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { buscarMedicos, buscarPacientes, crearPaciente, crearSolicitud } from '../api/laboratorioApi.js'
import { useEstudiosCatalogo } from '../hooks/useEstudiosCatalogo.js'
import ConfirmarAccion from './ConfirmarAccion.jsx'
import Dialogo from './Dialogo.jsx'
import DatosPedido from './nueva-solicitud/DatosPedido.jsx'
import EstudiosSolicitados from './nueva-solicitud/EstudiosSolicitados.jsx'
import PacienteSolicitud from './nueva-solicitud/PacienteSolicitud.jsx'
import { AREAS_LABORATORIO } from '../utils/catalogos.js'
import { mensajeError } from '../utils/mensajeError.js'
import { useValorDiferido } from '../../../shared/hooks/useValorDiferido.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import './formularios.css'

const PACIENTE_VACIO = {
  nombre_completo: '',
  fecha_nacimiento: '',
  sexo: 'no_especificado',
  tipo_documento: 'CI',
  numero_documento: '',
  sin_documento: false,
  historia_clinica: '',
  codigo_externo: '',
  telefono: '',
}

// Función, no constante: la fecha de hoy se calcula al abrir el formulario.
const pedidoInicial = () => ({
  referencia_papel_formulario: '',
  fecha_solicitud: new Date().toLocaleDateString('en-CA'),
  procedencia: 'este_centro',
  establecimiento_solicitante_nombre: '',
  medico_solicitante_nombre: '',
  medico_solicitante_id: null,
  diagnostico_principal: '',
  prioridad: 'sin_prioridad',
})

const GRUPOS_ESTUDIOS = [...AREAS_LABORATORIO, { codigo: null, nombre: 'Prestaciones por clasificar' }]

function validarPaciente(datos) {
  if (datos.nombre_completo.trim().length < 2) return 'Escribe el nombre completo del paciente.'
  if (!datos.fecha_nacimiento) return 'Selecciona la fecha de nacimiento del paciente.'
  if (!datos.sin_documento && (!datos.tipo_documento.trim() || !datos.numero_documento.trim())) {
    return 'Ingresa el documento o marca “Persona sin documento”.'
  }
  return null
}

function validarSolicitud(paciente, estudioIds, pedido) {
  if (!paciente) return 'Busca y selecciona un paciente antes de continuar.'
  if (pedido.procedencia === 'este_centro' && !pedido.medico_solicitante_id) return 'Selecciona un médico de Sarcobamba de la lista.'
  if (!estudioIds.length) return 'Selecciona al menos un estudio.'
  return null
}

export default function NuevaSolicitud({ onClose, onCreated }) {
  const queryClient = useQueryClient()
  const { notificar } = useNotificacion()
  const claveIdempotencia = useRef(crypto.randomUUID())
  const [termino, setTermino] = useState('')
  const [paciente, setPaciente] = useState(null)
  const [nuevoPaciente, setNuevoPaciente] = useState(false)
  const [datosPaciente, setDatosPaciente] = useState(PACIENTE_VACIO)
  const [estudioIds, setEstudioIds] = useState([])
  const [busquedaEstudio, setBusquedaEstudio] = useState('')
  const [pedido, setPedido] = useState(pedidoInicial)
  const [errorLocal, setErrorLocal] = useState('')
  const [confirmarCierre, setConfirmarCierre] = useState(false)
  const terminoPaciente = useValorDiferido(termino.trim())
  const terminoMedico = useValorDiferido(pedido.medico_solicitante_nombre.trim())

  const catalogoQuery = useEstudiosCatalogo()
  const pacientesQuery = useQuery({
    queryKey: ['laboratorio', 'pacientes', terminoPaciente],
    queryFn: () => buscarPacientes(terminoPaciente),
    enabled: terminoPaciente.length >= 2 && !nuevoPaciente,
  })
  const medicosQuery = useQuery({
    queryKey: ['laboratorio', 'medicos', terminoMedico],
    queryFn: () => buscarMedicos(terminoMedico),
    enabled: pedido.procedencia === 'este_centro' && !pedido.medico_solicitante_id && terminoMedico.length >= 2,
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
    onError: (error) => setErrorLocal(mensajeError(error, 'No se pudo registrar el paciente. Comprueba los datos e inténtalo nuevamente.')),
  })
  const crearSolicitudMutation = useMutation({
    mutationFn: crearSolicitud,
    onSuccess: async (solicitud) => {
      await queryClient.invalidateQueries({ queryKey: ['examenes'] })
      await queryClient.invalidateQueries({ queryKey: ['laboratorio'] })
      notificar(`Solicitud ${solicitud.referencia} registrada.`, 'exito')
      onCreated?.(solicitud)
      onClose()
    },
    onError: (error) => setErrorLocal(mensajeError(error, 'No se pudo registrar la solicitud.')),
  })

  const hayDatos = Boolean(paciente || nuevoPaciente || termino.trim() || estudioIds.length
    || pedido.medico_solicitante_nombre.trim() || pedido.referencia_papel_formulario.trim() || pedido.diagnostico_principal.trim())
  const ocupado = crearSolicitudMutation.isPending || crearPacienteMutation.isPending
  const solicitarCierre = () => (hayDatos ? setConfirmarCierre(true) : onClose())

  const cambiarPedido = (campo, valor) => setPedido((actual) => ({
    ...actual, [campo]: valor,
    ...(campo === 'procedencia' || campo === 'medico_solicitante_nombre' ? { medico_solicitante_id: null } : {}),
  }))
  const cambiarPaciente = (campo, valor) => setDatosPaciente((actual) => (campo === 'sin_documento' && valor
    ? { ...actual, sin_documento: true, tipo_documento: '', numero_documento: '' }
    : { ...actual, [campo]: valor, ...(campo === 'sin_documento' ? { tipo_documento: 'CI' } : {}) }))
  const alternarEstudio = (id) => setEstudioIds((actual) =>
    actual.includes(id) ? actual.filter((item) => item !== id) : [...actual, id])

  function enviar(evento) {
    evento.preventDefault()
    const error = validarSolicitud(paciente, estudioIds, pedido)
    setErrorLocal(error ?? '')
    if (error) return
    crearSolicitudMutation.mutate({
      ...pedido,
      fecha_solicitud: new Date(`${pedido.fecha_solicitud}T12:00:00`).toISOString(),
      paciente_id: paciente.id,
      tipo_estudio_ids: estudioIds,
      clave_idempotencia: claveIdempotencia.current,
    })
  }

  function registrarPaciente(evento) {
    evento.preventDefault()
    const error = validarPaciente(datosPaciente)
    setErrorLocal(error ?? '')
    if (error) return
    crearPacienteMutation.mutate({
      ...datosPaciente,
      nombre_completo: datosPaciente.nombre_completo.trim(),
      tipo_documento: datosPaciente.sin_documento ? null : datosPaciente.tipo_documento.trim(),
      numero_documento: datosPaciente.sin_documento ? null : datosPaciente.numero_documento.trim(),
      historia_clinica: datosPaciente.historia_clinica.trim() || null,
      codigo_externo: datosPaciente.codigo_externo.trim() || null,
      telefono: datosPaciente.telefono.trim() || null,
    })
  }

  const catalogo = catalogoQuery.data ?? []
  const terminoEstudio = busquedaEstudio.trim().toLocaleLowerCase()
  const estudiosVisibles = catalogo.filter((item) => item.nombre.toLocaleLowerCase().includes(terminoEstudio))
  const grupos = GRUPOS_ESTUDIOS
    .map((grupo) => ({ ...grupo, estudios: estudiosVisibles.filter((item) => item.categoria_laboratorio === grupo.codigo) }))
    .filter((grupo) => grupo.estudios.length > 0)
  const seleccionados = estudioIds.map((id) => catalogo.find((estudio) => estudio.id === id)).filter(Boolean)

  return <>
    <Dialogo eyebrow="D-8 · SOLICITUD DE EXÁMENES" titulo="Nueva solicitud" bloqueado={ocupado}
      descripcion="Identifica al paciente y registra los estudios que llegaron en el pedido." onCerrar={solicitarCierre}>
      <form onSubmit={enviar}>
        <div className="lab-dialog-body">
          <PacienteSolicitud
            paciente={paciente} nuevoPaciente={nuevoPaciente} datosPaciente={datosPaciente}
            termino={termino} buscando={termino.trim() !== terminoPaciente || pacientesQuery.isFetching}
            pacientesQuery={pacientesQuery} crearPacientePendiente={crearPacienteMutation.isPending}
            onSelect={(seleccionado) => { setPaciente(seleccionado); setErrorLocal('') }}
            onTerminoChange={setTermino} onStartCreate={() => setNuevoPaciente(true)}
            onCancelCreate={() => setNuevoPaciente(false)} onPacienteChange={cambiarPaciente}
            onCreatePaciente={registrarPaciente}
          />
          <DatosPedido datos={pedido} onChange={cambiarPedido} medicosQuery={medicosQuery}
            onSeleccionarMedico={(medico) => setPedido((actual) => ({
              ...actual, medico_solicitante_id: medico.id, medico_solicitante_nombre: medico.nombre,
            }))} />
          <EstudiosSolicitados
            cargando={catalogoQuery.isLoading} error={catalogoQuery.isError} catalogo={catalogo}
            busqueda={busquedaEstudio} onBusquedaChange={setBusquedaEstudio}
            seleccionados={seleccionados} idsSeleccionados={estudioIds}
            grupos={grupos} hayResultados={estudiosVisibles.length > 0} onToggle={alternarEstudio}
          />
          {errorLocal && <p className="lab-form-error" role="alert">{errorLocal}</p>}
        </div>
        <footer className="lab-dialog-footer">
          <p className="lab-dialog-summary">
            {paciente ? <strong>{paciente.nombre_completo}</strong> : 'Sin paciente'} · {estudioIds.length} {estudioIds.length === 1 ? 'estudio' : 'estudios'}
            {pedido.prioridad === 'urgente' && <strong className="lab-priority"> · Urgente</strong>}
          </p>
          <button type="button" onClick={solicitarCierre} disabled={ocupado}>Cancelar</button>
          <button className="primary-button" type="submit" disabled={ocupado || !catalogo.length}>
            {crearSolicitudMutation.isPending ? 'Registrando…' : 'Registrar solicitud'}
          </button>
        </footer>
      </form>
    </Dialogo>
    {confirmarCierre && <ConfirmarAccion titulo="¿Descartar la solicitud?" textoConfirmar="Descartar" textoCancelar="Seguir editando" peligro
      onConfirmar={onClose} onCancelar={() => setConfirmarCierre(false)}>
      <p>Los datos que ingresaste en esta solicitud se perderán.</p>
    </ConfirmarAccion>}
  </>
}
