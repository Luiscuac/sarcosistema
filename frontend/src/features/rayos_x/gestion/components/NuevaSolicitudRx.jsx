import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { buscarMedicos, buscarPacientes, crearPaciente, crearSolicitud, mensajeErrorApi, obtenerCatalogo } from '../../api/radiologiaApi.js'
import ConfirmarAccion from '../../../laboratorio/components/ConfirmarAccion.jsx'
import { nombreSexo, SEXOS, TIPOS_DOCUMENTO } from '../../../laboratorio/utils/catalogos.js'
import { describirEdad } from '../../../../shared/utils/edad.js'
import { formatearFecha } from '../../../../shared/utils/formatearFecha.js'
import { useValorDiferido } from '../../../../shared/hooks/useValorDiferido.js'
import { CatalogoEstudiosRx, EstudiosSeleccionadosRx } from './SelectorEstudiosRx.jsx'
import { erroresDeSolicitud, prepararEstudiosParaApi } from '../utils/solicitud.js'

const PACIENTE_VACIO = {
  nombre_completo: '', fecha_nacimiento: '', sexo: 'no_especificado', tipo_documento: 'CI',
  numero_documento: '', sin_documento: false, historia_clinica: '', codigo_externo: '', telefono: '',
}

const PEDIDO_INICIAL = {
  procedencia: 'este_centro', medico_solicitante_id: null, medico_solicitante_nombre: '',
  establecimiento_solicitante_nombre: '', prioridad: 'sin_prioridad', diagnostico_principal: '',
}

function detallePaciente(paciente) {
  return [
    paciente.numero_documento ? `Doc. ${paciente.numero_documento}` : 'Sin documento',
    paciente.fecha_nacimiento && `${describirEdad(paciente.fecha_nacimiento)} (${formatearFecha(paciente.fecha_nacimiento)})`,
    paciente.sexo && nombreSexo(paciente.sexo),
    paciente.historia_clinica && `HC ${paciente.historia_clinica}`,
    paciente.codigo_externo && `Código interno ${paciente.codigo_externo}`,
  ].filter(Boolean).join(' · ')
}

function errorPaciente(datos) {
  if (datos.nombre_completo.trim().length < 2) return 'Escribe el nombre completo del paciente.'
  if (!datos.fecha_nacimiento) return 'Selecciona la fecha de nacimiento del paciente.'
  if (!datos.sin_documento && (!datos.tipo_documento.trim() || !datos.numero_documento.trim())) return 'Ingresa el documento o marca "Persona sin documento".'
  return ''
}

export default function NuevaSolicitudRx({ onClose, onCreated }) {
  const queryClient = useQueryClient()
  const claveIdempotencia = useRef(crypto.randomUUID())
  const [terminoPaciente, setTerminoPaciente] = useState('')
  const [paciente, setPaciente] = useState(null)
  const [registrandoPaciente, setRegistrandoPaciente] = useState(false)
  const [datosPaciente, setDatosPaciente] = useState(PACIENTE_VACIO)
  const [estudios, setEstudios] = useState([])
  const [pedido, setPedido] = useState(PEDIDO_INICIAL)
  const [errores, setErrores] = useState([])
  const avisoErrores = useRef(null)
  useEffect(() => { if (errores.length) avisoErrores.current?.scrollIntoView({ block: 'center', behavior: 'smooth' }) }, [errores])
  const [confirmarRegistro, setConfirmarRegistro] = useState(false)
  const [confirmarCierre, setConfirmarCierre] = useState(false)
  const pacienteDiferido = useValorDiferido(terminoPaciente.trim())
  const medicoDiferido = useValorDiferido(pedido.medico_solicitante_nombre.trim())

  const catalogoQuery = useQuery({ queryKey: ['radiologia', 'catalogo'], queryFn: () => obtenerCatalogo() })
  const pacientesQuery = useQuery({
    queryKey: ['radiologia', 'pacientes', pacienteDiferido],
    queryFn: ({ signal }) => buscarPacientes(pacienteDiferido, signal),
    enabled: pacienteDiferido.length >= 2 && !registrandoPaciente && !paciente,
  })
  const medicosQuery = useQuery({
    queryKey: ['radiologia', 'medicos', medicoDiferido],
    queryFn: ({ signal }) => buscarMedicos(medicoDiferido, signal),
    enabled: pedido.procedencia === 'este_centro' && !pedido.medico_solicitante_id && medicoDiferido.length >= 2,
  })
  const pacienteMutation = useMutation({
    mutationFn: crearPaciente,
    onSuccess: (creado) => {
      setPaciente(creado)
      setRegistrandoPaciente(false)
      setTerminoPaciente('')
      setErrores([])
      queryClient.invalidateQueries({ queryKey: ['radiologia', 'pacientes'] })
    },
    onError: (error) => setErrores([mensajeErrorApi(error, 'No se pudo registrar el paciente.')]),
  })
  const solicitudMutation = useMutation({
    mutationFn: crearSolicitud,
    onSuccess: async (respuesta) => {
      await queryClient.invalidateQueries({ queryKey: ['radiologia', 'estudios'] })
      if (onCreated) onCreated(respuesta)
      else onClose()
    },
    onError: (error) => {
      setConfirmarRegistro(false)
      setErrores([mensajeErrorApi(error, 'No se pudo registrar la solicitud.')])
    },
  })

  const hayDatos = Boolean(paciente || registrandoPaciente || terminoPaciente.trim() || estudios.length
    || pedido.medico_solicitante_nombre.trim() || pedido.establecimiento_solicitante_nombre.trim()
    || pedido.diagnostico_principal.trim() || pedido.prioridad === 'urgente')
  const ocupado = pacienteMutation.isPending || solicitudMutation.isPending

  function cambiarPaciente(campo, valor) {
    setDatosPaciente((actual) => campo === 'sin_documento' && valor
      ? { ...actual, sin_documento: true, tipo_documento: '', numero_documento: '' }
      : { ...actual, [campo]: valor, ...(campo === 'sin_documento' ? { tipo_documento: 'CI' } : {}) })
  }

  function registrarPaciente() {
    const mensaje = errorPaciente(datosPaciente)
    if (mensaje) return setErrores([mensaje])
    setErrores([])
    pacienteMutation.mutate({
      ...datosPaciente,
      nombre_completo: datosPaciente.nombre_completo.trim(),
      tipo_documento: datosPaciente.sin_documento ? null : datosPaciente.tipo_documento.trim(),
      numero_documento: datosPaciente.sin_documento ? null : datosPaciente.numero_documento.trim(),
      historia_clinica: datosPaciente.historia_clinica.trim() || null,
      codigo_externo: datosPaciente.codigo_externo.trim() || null,
      telefono: datosPaciente.telefono.trim() || null,
    })
  }

  function cambiarPedido(campo, valor) {
    setPedido((actual) => ({
      ...actual, [campo]: valor,
      ...(['procedencia', 'medico_solicitante_nombre'].includes(campo) ? { medico_solicitante_id: null } : {}),
      ...(campo === 'procedencia' ? { medico_solicitante_nombre: '', establecimiento_solicitante_nombre: '' } : {}),
    }))
  }

  function revisar(evento) {
    evento.preventDefault()
    const encontrados = erroresDeSolicitud({ catalogo: catalogoQuery.data, paciente, estudios, pedido })
    setErrores(encontrados)
    if (!encontrados.length) setConfirmarRegistro(true)
  }

  function confirmar() {
    solicitudMutation.mutate({
      paciente_id: paciente.id,
      prioridad: pedido.prioridad,
      procedencia: pedido.procedencia,
      medico_solicitante_id: pedido.procedencia === 'este_centro' ? pedido.medico_solicitante_id : null,
      medico_solicitante_nombre: pedido.procedencia === 'otro_centro' ? pedido.medico_solicitante_nombre.trim() : null,
      establecimiento_solicitante_nombre: pedido.procedencia === 'otro_centro' ? pedido.establecimiento_solicitante_nombre.trim() : null,
      diagnostico_principal: pedido.diagnostico_principal.trim() || null,
      clave_idempotencia: claveIdempotencia.current,
      estudios: prepararEstudiosParaApi(estudios),
    })
  }

  const resultadosPacientes = pacientesQuery.data ?? []
  const pedidoListo = Boolean(pedido.procedencia === 'este_centro' ? pedido.medico_solicitante_id : pedido.medico_solicitante_nombre.trim() && pedido.establecimiento_solicitante_nombre.trim())
  const pasos = [
    { nombre: 'Paciente', listo: Boolean(paciente), detalle: paciente ? paciente.nombre_completo : 'Sin elegir' },
    { nombre: 'Estudios', listo: estudios.length > 0, detalle: estudios.length ? `${estudios.length} ${estudios.length === 1 ? 'elegido' : 'elegidos'}` : 'Ninguno' },
    { nombre: 'Pedido', listo: pedidoListo, detalle: pedidoListo ? (pedido.prioridad === 'urgente' ? 'Urgente' : 'Completo') : 'Falta el médico solicitante' },
  ]
  const solicitarCierre = () => hayDatos ? setConfirmarCierre(true) : onClose()

  return <>
    <form className="rxg-nueva" onSubmit={revisar}>
      <ol className="rxg-pasos" aria-label="Avance de la solicitud">
        {pasos.map((paso, indice) => <li key={paso.nombre} data-listo={paso.listo}>
          <span className="rxg-paso-marca" aria-hidden="true">{paso.listo ? '✓' : indice + 1}</span>
          <span className="rxg-paso-texto"><strong>{paso.nombre}</strong><small>{paso.detalle}<span className="rxg-sr">{paso.listo ? ' (completo)' : ' (pendiente)'}</span></small></span>
        </li>)}
      </ol>
      <div className="rxg-nueva-columnas">
        <div className="rxg-nueva-izquierda">
          <section className="lab-form-section">
            <h3>1. Paciente</h3>
            {paciente ? <div className="rxg-paciente-seleccionado">
              <div><strong>{paciente.nombre_completo}</strong><span>{detallePaciente(paciente)}</span></div>
              <button type="button" onClick={() => setPaciente(null)}>Cambiar</button>
            </div> : registrandoPaciente ? <div className="rxg-paciente-form">
              <div className="lab-form-grid">
                <label className="lab-full-field">Nombre completo<input required minLength="2" autoFocus value={datosPaciente.nombre_completo} onChange={(e) => cambiarPaciente('nombre_completo', e.target.value)} /></label>
                <label>Fecha de nacimiento<input required type="date" max={new Date().toLocaleDateString('en-CA')} value={datosPaciente.fecha_nacimiento} onChange={(e) => cambiarPaciente('fecha_nacimiento', e.target.value)} />{datosPaciente.fecha_nacimiento && <small>{describirEdad(datosPaciente.fecha_nacimiento)}</small>}</label>
                <label>Sexo registrado<select value={datosPaciente.sexo} onChange={(e) => cambiarPaciente('sexo', e.target.value)}>{SEXOS.map((sexo) => <option key={sexo.codigo} value={sexo.codigo}>{sexo.nombre}</option>)}</select></label>
                <label className="lab-checkbox-label lab-full-field"><input type="checkbox" checked={datosPaciente.sin_documento} onChange={(e) => cambiarPaciente('sin_documento', e.target.checked)} /> Persona sin documento</label>
                {!datosPaciente.sin_documento && <><label>Tipo de documento<select required value={datosPaciente.tipo_documento} onChange={(e) => cambiarPaciente('tipo_documento', e.target.value)}>{TIPOS_DOCUMENTO.map((tipo) => <option key={tipo}>{tipo}</option>)}</select></label><label>Número de documento<input required value={datosPaciente.numero_documento} onChange={(e) => cambiarPaciente('numero_documento', e.target.value)} /></label></>}
                <label>N.º de historia clínica (opcional)<input maxLength="80" value={datosPaciente.historia_clinica} onChange={(e) => cambiarPaciente('historia_clinica', e.target.value)} /></label>
                <label>Código interno (opcional)<input maxLength="80" value={datosPaciente.codigo_externo} onChange={(e) => cambiarPaciente('codigo_externo', e.target.value)} /></label>
                <label>Teléfono (opcional)<input type="tel" maxLength="40" value={datosPaciente.telefono} onChange={(e) => cambiarPaciente('telefono', e.target.value)} /></label>
              </div>
              <div className="rxg-inline-actions"><button type="button" onClick={() => setRegistrandoPaciente(false)}>Volver a buscar</button><button className="primary-button" type="button" disabled={pacienteMutation.isPending} onClick={registrarPaciente}>{pacienteMutation.isPending ? 'Guardando...' : 'Guardar paciente'}</button></div>
            </div> : <>
              <label className="lab-search-label">Buscar por nombre, documento, historia clínica o código
                <input autoFocus type="search" value={terminoPaciente} onChange={(e) => setTerminoPaciente(e.target.value)} placeholder="Escribe al menos 2 caracteres" />
              </label>
              {terminoPaciente.trim().length >= 2 && (pacientesQuery.isFetching || terminoPaciente.trim() !== pacienteDiferido) && <p className="lab-form-hint">Buscando pacientes...</p>}
              {pacientesQuery.isError && <p className="lab-form-error" role="alert">{mensajeErrorApi(pacientesQuery.error, 'No se pudo buscar pacientes.')}</p>}
              {resultadosPacientes.map((item) => <button className="rxg-opcion-persona" type="button" key={item.id} onClick={() => { setPaciente(item); setErrores([]) }}><strong>{item.nombre_completo}</strong><span>{detallePaciente(item)}</span></button>)}
              {pacientesQuery.isSuccess && !pacientesQuery.isFetching && pacienteDiferido.length >= 2 && resultadosPacientes.length === 0 && <p className="lab-form-hint">No se encontró el paciente. Revisa la escritura o regístralo.</p>}
              <button className="rxg-text-button" type="button" onClick={() => setRegistrandoPaciente(true)}>Registrar paciente nuevo</button>
            </>}
          </section>

          <CatalogoEstudiosRx catalogo={catalogoQuery.data} valor={estudios} onChange={setEstudios} deshabilitado={ocupado} />
          {catalogoQuery.isError && <p className="lab-form-error" role="alert">{mensajeErrorApi(catalogoQuery.error, 'No se pudo cargar el catálogo de Rayos X.')}</p>}
        </div>
        <aside className="rxg-nueva-derecha">
          <EstudiosSeleccionadosRx catalogo={catalogoQuery.data} valor={estudios} onChange={setEstudios} deshabilitado={ocupado} titulo={estudios.length ? `Estudios seleccionados (${estudios.length})` : 'Estudios seleccionados'} />
          <section className="lab-form-section">
            <h3>3. Datos del pedido</h3>
            <div className="lab-form-grid">
              <label>Procedencia<select value={pedido.procedencia} onChange={(e) => cambiarPedido('procedencia', e.target.value)}><option value="este_centro">Este centro</option><option value="otro_centro">Otro centro</option></select></label>
              <label>Prioridad<select value={pedido.prioridad} onChange={(e) => cambiarPedido('prioridad', e.target.value)}><option value="sin_prioridad">Sin prioridad</option><option value="urgente">Urgente</option></select></label>
              {pedido.procedencia === 'otro_centro' && <label className="lab-full-field">Establecimiento externo<input required value={pedido.establecimiento_solicitante_nombre} onChange={(e) => cambiarPedido('establecimiento_solicitante_nombre', e.target.value)} /></label>}
              {pedido.procedencia === 'este_centro' && pedido.medico_solicitante_id ? <div className="rxg-medico-seleccionado"><span className="lab-field-label">Médico solicitante</span><span className="lab-chip">{pedido.medico_solicitante_nombre}<button type="button" onClick={() => cambiarPedido('medico_solicitante_nombre', '')}>Cambiar</button></span></div> : <label className="lab-full-field">Médico solicitante<input required autoComplete="off" value={pedido.medico_solicitante_nombre} onChange={(e) => cambiarPedido('medico_solicitante_nombre', e.target.value)} placeholder={pedido.procedencia === 'este_centro' ? 'Escribe y elige de la lista' : 'Nombre del médico'} /></label>}
              {pedido.procedencia === 'este_centro' && !pedido.medico_solicitante_id && medicoDiferido.length >= 2 && <div className="lab-full-field">
                {medicosQuery.isFetching && <p className="lab-form-hint">Buscando médicos...</p>}
                {medicosQuery.isError && <p className="lab-form-error" role="alert">{mensajeErrorApi(medicosQuery.error, 'No se pudo buscar médicos.')}</p>}
                {(medicosQuery.data ?? []).map((medico) => <button className="rxg-opcion-persona" type="button" key={medico.id} onClick={() => setPedido((actual) => ({ ...actual, medico_solicitante_id: medico.id, medico_solicitante_nombre: medico.nombre }))}><strong>{medico.nombre}</strong></button>)}
              </div>}
              <label className="lab-full-field">Diagnóstico o motivo general (opcional)<textarea rows="3" value={pedido.diagnostico_principal} onChange={(e) => cambiarPedido('diagnostico_principal', e.target.value)} /></label>
            </div>
          </section>
          {errores.length > 0 && <div className="rxg-errores" role="alert" ref={avisoErrores}><strong>Revisa la solicitud:</strong><ul>{errores.map((error) => <li key={error}>{error}</li>)}</ul></div>}
          <div className="rxg-nueva-acciones">
            <p className="lab-dialog-summary">{paciente ? <strong>{paciente.nombre_completo}</strong> : 'Sin paciente'} · {estudios.length} {estudios.length === 1 ? 'estudio' : 'estudios'}{pedido.prioridad === 'urgente' && ' · Urgente'}</p>
            <button type="button" className="lab-secondary-button" onClick={solicitarCierre} disabled={ocupado}>Cancelar</button>
            <button className="primary-button" type="submit" disabled={ocupado || catalogoQuery.isLoading}>Revisar solicitud</button>
          </div>
        </aside>
      </div>
    </form>
    {confirmarRegistro && <ConfirmarAccion titulo="Confirmar nueva solicitud" textoConfirmar="Registrar solicitud" pendiente={solicitudMutation.isPending} onConfirmar={confirmar} onCancelar={() => setConfirmarRegistro(false)}>
      <p>Se registrará la solicitud para <strong>{paciente?.nombre_completo}</strong> con {estudios.length} {estudios.length === 1 ? 'estudio' : 'estudios'}.</p>
      <p>Prioridad: <strong>{pedido.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'}</strong>.</p>
      <div className="lab-confirm-study"><h3>Resumen de estudios</h3><ul>{estudios.map((seleccion, indice) => {
        const estudio = catalogoQuery.data?.estudios?.find((item) => Number(item.id) === Number(seleccion.tipo_estudio_id))
        const lateralidad = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }[seleccion.lateralidad]
        return <li key={`${seleccion.tipo_estudio_id}-${indice}`}>{estudio?.nombre ?? 'Estudio'}{lateralidad ? ` · ${lateralidad}` : ''}</li>
      })}</ul></div>
      <p>Solicitante: <strong>{pedido.medico_solicitante_nombre}</strong>{pedido.procedencia === 'otro_centro' && ` · ${pedido.establecimiento_solicitante_nombre}`}.</p>
    </ConfirmarAccion>}
    {confirmarCierre && <ConfirmarAccion titulo="¿Descartar la solicitud?" textoConfirmar="Descartar" textoCancelar="Seguir editando" peligro onConfirmar={onClose} onCancelar={() => setConfirmarCierre(false)}><p>Los datos ingresados se perderán.</p></ConfirmarAccion>}
  </>
}
