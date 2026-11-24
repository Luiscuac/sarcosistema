import { useEffect, useRef, useState } from 'react'
import { useBlocker, useLocation, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  actualizarBorradorEnfermeria, buscarPacientesEnfermeria, crearPacienteEnfermeria,
  guardarBorradorEnfermeria, obtenerRecetasRecibidasEnfermeria, obtenerRegistrosEnfermeria,
  publicarRegistroEnfermeria,
} from '../api/enfermeriaApi.js'
import { FormularioPaciente } from '../../laboratorio/components/nueva-solicitud/PacienteSolicitud.jsx'
import './enfermeria.css'
import RecetasRecibidas from '../components/RecetasRecibidas.jsx'
import FormularioAdmision from '../components/FormularioAdmision.jsx'
import ConfirmarAccion from '../../../shared/ui/ConfirmarAccion.jsx'
import BarraSuperior from '../../../shared/ui/BarraSuperior.jsx'
import { nombreSexo } from '../../../shared/utils/personas.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import { calcularEdad, describirEdad } from '../../../shared/utils/edad.js'
import Boton from '../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../shared/utils/mensajeError.js'
import {
  FORMULARIO_VACIO, MEDICIONES, TEXTOS, cuerpoDesdeFormulario, erroresDelFormulario,
  formularioDesdeRegistro, formularioVacio, resumenDelFormulario,
} from '../utils/signosVitales.js'
import { formatearFechaHora } from '../../../shared/utils/formatearFecha.js'
import NavegacionPagina from '../../../shared/ui/NavegacionPagina.jsx'

const fechaHora = (value) => value ? formatearFechaHora(value) : 'Sin fecha'
const etiquetasCampos = {
  ...Object.fromEntries(TEXTOS),
  ...Object.fromEntries(Object.entries(MEDICIONES).map(([campo, { etiqueta }]) => [campo, etiqueta])),
  presion_sistolica: 'Presión sistólica', presion_diastolica: 'Presión diastólica', dolor_escala: 'Dolor',
}
/** Errores de validación con el nombre del campo de signos vitales; lo demás, el mensaje estándar. */
function mensajeErrorRegistro(error, porDefecto) {
  const detalle = error.response?.data?.detail
  if (Array.isArray(detalle)) return detalle.map((item) => {
    const campo = item.loc?.at(-1)
    const etiqueta = etiquetasCampos[campo]
    const mensaje = String(item.msg || 'Dato no válido').replace(/^Value error, /, '')
    return `${etiqueta ? `${etiqueta}: ` : ''}${mensaje}`
  }).join(' ')
  return mensajeError(error, porDefecto)
}
const edadTexto = (nacimiento) => describirEdad(nacimiento) || 'Edad no registrada'
const MENSAJE_PUBLICADO = 'Registro publicado. Ya está disponible en la ficha médica del paciente.'
const PACIENTE_VACIO = {
  nombre_completo: '', fecha_nacimiento: '', sexo: 'no_especificado',
  tipo_documento: 'CI', numero_documento: '', sin_documento: false,
  historia_clinica: '', codigo_externo: '', telefono: '',
}

function ResumenValores({ lineas }) {
  return <dl className="enf-summary">{lineas.map(({ campo, etiqueta, valor }) =>
    <div key={campo}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
}

function RegistroResumen({ registro, editando, onAbrir, ocupado }) {
  const lineas = resumenDelFormulario(formularioDesdeRegistro(registro))
  const motivo = lineas.find(({ campo }) => campo === 'motivo_consulta')
    || lineas.find(({ campo }) => campo === 'sintomas')
    || lineas.find(({ campo }) => TEXTOS.some(([nombre]) => nombre === campo))
  const estado = registro.estado === 'publicado' ? 'Publicado' : editando ? 'Borrador · en edición' : 'Borrador'
  return <article className="enf-history-list-item">
    <div className="enf-history-list-main">
      <strong>Admisión de enfermería</strong>
      <span>{fechaHora(registro.publicado_en || registro.creado_en)} · {estado}</span>
    </div>
    <p><span>{motivo?.etiqueta || 'Motivo referido'}</span>{motivo?.valor || 'Valoración registrada'}</p>
    <button type="button" className="enf-history-open" onClick={() => onAbrir(registro)} disabled={ocupado}>
      Ver informe <span aria-hidden="true">→</span>
    </button>
  </article>
}

export default function EnfermeriaPage({ usuario, logout }) {
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const location = useLocation()
  const navigate = useNavigate()
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)
  const [nuevoPaciente, setNuevoPaciente] = useState(false)
  const [datosPaciente, setDatosPaciente] = useState(PACIENTE_VACIO)
  const [errorPaciente, setErrorPaciente] = useState('')
  const [paciente, setPaciente] = useState(() => location.state?.paciente || null)
  const [buscando, setBuscando] = useState(() => !location.state?.paciente)
  const [form, setForm] = useState(() => location.state?.edicion
    ? formularioDesdeRegistro(location.state.edicion)
    : FORMULARIO_VACIO)
  const [edicion, setEdicion] = useState(() => location.state?.edicion || null)
  const [ocupado, setOcupado] = useState(false)
  const [iaBloqueada, setIaBloqueada] = useState(false)
  const [error, setError] = useState('')
  const [pantalla, setPantalla] = useState(() => location.state?.pantalla || 'admision')
  // { origen: 'formulario' } publica lo que está en pantalla; { origen: 'registro', registro } un borrador ya guardado.
  const [confirmacion, setConfirmacion] = useState(null)
  // Descarte de datos sin guardar: { tipo: 'paciente', paciente } | { tipo: 'salir' }.
  const [descarte, setDescarte] = useState(null)
  const panelFormulario = useRef(null)
  const salidaConfirmada = useRef(false)

  const hayCambios = !formularioVacio(form)
  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    hayCambios && !salidaConfirmada.current && currentLocation.pathname !== nextLocation.pathname)

  useEffect(() => {
    const timer = setTimeout(() => { setBuscar(entrada.trim()); setPagina(1) }, 350)
    return () => clearTimeout(timer)
  }, [entrada])

  // Cerrar o recargar la pestaña con datos sin guardar: aviso nativo del navegador (no se puede personalizar).
  useEffect(() => {
    if (!hayCambios) return undefined
    const avisar = (evento) => { evento.preventDefault(); evento.returnValue = '' }
    window.addEventListener('beforeunload', avisar)
    return () => window.removeEventListener('beforeunload', avisar)
  }, [hayCambios])

  const pacientes = useQuery({
    queryKey: ['enfermeria', 'pacientes', buscar, pagina],
    queryFn: () => buscarPacientesEnfermeria(buscar, pagina),
    enabled: buscando && buscar.length >= 2,
  })
  const registros = useQuery({
    queryKey: ['enfermeria', 'registros', paciente?.id],
    queryFn: () => obtenerRegistrosEnfermeria(paciente.id),
    enabled: Boolean(paciente?.id),
  })
  // Misma clave que RecetasRecibidas: se comparte la caché y el contador no hace otra petición.
  const recetas = useQuery({
    queryKey: ['enfermeria', 'recetas-recibidas', paciente?.id],
    queryFn: () => obtenerRecetasRecibidasEnfermeria(paciente.id),
    enabled: Boolean(paciente?.id),
  })
  const termino = entrada.trim()
  const esperandoBusqueda = termino !== buscar
  const erroresForm = erroresDelFormulario(form)
  const edad = calcularEdad(paciente?.fecha_nacimiento)

  function cambiarCampo(campo, valor) {
    setForm((actual) => ({ ...actual, [campo]: valor }))
  }

  function cambiarDatosPaciente(campo, valor) {
    setDatosPaciente((actual) => (campo === 'sin_documento' && valor
      ? { ...actual, sin_documento: true, tipo_documento: '', numero_documento: '' }
      : { ...actual, [campo]: valor, ...(campo === 'sin_documento' ? { tipo_documento: 'CI' } : {}) }))
    setErrorPaciente('')
  }

  async function registrarPaciente() {
    if (ocupado) return
    if (datosPaciente.nombre_completo.trim().length < 2) {
      setErrorPaciente('Escribe el nombre completo del paciente.')
      return
    }
    if (!datosPaciente.fecha_nacimiento) {
      setErrorPaciente('Selecciona la fecha de nacimiento del paciente.')
      return
    }
    if (!datosPaciente.sin_documento && (!datosPaciente.tipo_documento.trim() || !datosPaciente.numero_documento.trim())) {
      setErrorPaciente('Ingresa el documento o marca “Persona sin documento”.')
      return
    }
    setOcupado(true)
    setErrorPaciente('')
    try {
      const creado = await crearPacienteEnfermeria({
        ...datosPaciente,
        nombre_completo: datosPaciente.nombre_completo.trim(),
        tipo_documento: datosPaciente.sin_documento ? null : datosPaciente.tipo_documento.trim(),
        numero_documento: datosPaciente.sin_documento ? null : datosPaciente.numero_documento.trim(),
        historia_clinica: datosPaciente.historia_clinica.trim() || null,
        codigo_externo: datosPaciente.codigo_externo.trim() || null,
        telefono: datosPaciente.telefono.trim() || null,
      })
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'pacientes'] })
      abrirPaciente(creado)
      setEntrada('')
      notificar('Paciente registrado. Ya puedes completar su admisión.', 'exito')
    } catch (err) {
      setErrorPaciente(mensajeErrorRegistro(err, 'No se pudo registrar el paciente. Revisa los datos e inténtalo de nuevo.'))
    } finally {
      setOcupado(false)
    }
  }

  function limpiarFormulario() {
    setForm(FORMULARIO_VACIO); setEdicion(null)
  }

  function abrirPaciente(item) {
    setPaciente(item)
    setBuscando(false)
    setNuevoPaciente(false)
    setDatosPaciente(PACIENTE_VACIO)
    setErrorPaciente('')
    limpiarFormulario()
    setPantalla('admision')
    setError('')
  }

  function elegirPaciente(item) {
    if (item.id === paciente?.id) { setBuscando(false); return }
    if (hayCambios) setDescarte({ tipo: 'paciente', paciente: item })
    else abrirPaciente(item)
  }

  function salir() {
    if (hayCambios) setDescarte({ tipo: 'salir' })
    else logout()
  }

  function confirmarDescarte() {
    if (blocker.state === 'blocked') { blocker.proceed(); return }
    if (descarte?.tipo === 'paciente') abrirPaciente(descarte.paciente)
    if (descarte?.tipo === 'salir') { salidaConfirmada.current = true; limpiarFormulario(); logout() }
    setDescarte(null)
  }

  function cancelarDescarte() {
    if (blocker.state === 'blocked') blocker.reset()
    setDescarte(null)
  }

  function editarBorrador(registro) {
    setEdicion(registro)
    setForm(formularioDesdeRegistro(registro))
    setError('')
    setPantalla('admision')
    // Esperar al render para desplazar hasta el formulario y dejar el foco en el primer campo.
    window.requestAnimationFrame(() => {
      panelFormulario.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      panelFormulario.current?.querySelector('[data-campo-admision]')?.focus({ preventScroll: true })
    })
  }

  /** Guarda el formulario; con publicar=true pide confirmación con el resumen antes de enviar nada. */
  function guardar(publicar) {
    if (ocupado || iaBloqueada || !paciente) return
    if (!hayCambios) {
      setError('Registra al menos un dato de admisión o una medición antes de guardar.')
      return
    }
    if (erroresForm.length) {
      setError(`Corrige: ${erroresForm.map(([campo]) => (campo === 'presion' ? 'Presión arterial' : etiquetasCampos[campo])).join(', ')}.`)
      return
    }
    setError('')
    if (publicar) setConfirmacion({ origen: 'formulario' })
    else ejecutarGuardado(false)
  }

  async function ejecutarGuardado(publicar) {
    if (iaBloqueada) return
    setOcupado(true); setError('')
    let guardado = false
    try {
      const datos = cuerpoDesdeFormulario(form)
      const registro = edicion
        ? await actualizarBorradorEnfermeria(edicion.id, datos)
        : await guardarBorradorEnfermeria(paciente.id, datos)
      guardado = true
      if (publicar) await publicarRegistroEnfermeria(registro.id)
      limpiarFormulario()
      notificar(publicar ? MENSAJE_PUBLICADO : 'Borrador guardado. Puedes publicarlo desde la lista de registros.', 'exito')
    } catch (err) {
      if (guardado) {
        limpiarFormulario()
        notificar(`Se guardó como borrador, pero no se pudo publicar: ${mensajeErrorRegistro(err, 'inténtalo desde la lista de registros.')}`, 'error')
      } else {
        setError(mensajeErrorRegistro(err, 'No se pudo guardar. Revisa los datos e inténtalo de nuevo.'))
      }
    } finally {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', paciente.id] })
      if (guardado) setPantalla('registros')
      setOcupado(false); setConfirmacion(null)
    }
  }

  async function publicarBorrador(registro) {
    setOcupado(true); setError('')
    try {
      await publicarRegistroEnfermeria(registro.id)
      if (edicion?.id === registro.id) limpiarFormulario()
      notificar(MENSAJE_PUBLICADO, 'exito')
    } catch (err) {
      notificar(mensajeErrorRegistro(err, 'No se pudo publicar el registro.'), 'error')
    } finally {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', paciente.id] })
      setOcupado(false); setConfirmacion(null)
    }
  }

  const resumenConfirmacion = confirmacion?.origen === 'registro'
    ? resumenDelFormulario(formularioDesdeRegistro(confirmacion.registro))
    : resumenDelFormulario(form)
  const totalRecetas = recetas.data?.length
  const mostrarDescarte = blocker.state === 'blocked' || descarte

  return <main className="lab-page enf-page">
    <BarraSuperior usuario={usuario} titulo="Enfermería" inicio="/enfermeria" onLogout={salir} />
    <div className="enf-content">
      {paciente && !buscando && <NavegacionPagina onVolver={() => setBuscando(true)} textoVolver="Volver a la búsqueda"
        migas={[{ texto: 'Enfermería', onClick: () => setBuscando(true) }, { texto: paciente.nombre_completo }]} />}
      <div className="enf-heading"><div><p>ADMISIÓN Y VALORACIÓN INICIAL</p><h1>Registro de enfermería</h1><span>Captura datos referidos y mediciones. Revisa y publica para que el médico pueda consultarlos.</span></div></div>

      {paciente && !buscando
        ? <section className="enf-panel enf-patient-card">
          <div><p>PACIENTE SELECCIONADO</p><h2>{paciente.nombre_completo}</h2>
            <span>{edadTexto(paciente.fecha_nacimiento)} · {paciente.sexo ? nombreSexo(paciente.sexo) : 'Sexo no registrado'} · HC {paciente.historia_clinica || 'No registrada'} · {paciente.codigo_paciente} · {paciente.numero_documento || 'Sin documento'}</span></div>
          <button type="button" className="enf-change-patient" onClick={() => setBuscando(true)}>Cambiar paciente</button>
        </section>
        : <section className="enf-panel enf-search-workspace" aria-label="Búsqueda de pacientes">
          <div className="enf-panel-heading"><h2>Buscar paciente</h2>
            <div className="enf-search-heading-actions">
              {paciente && <button type="button" className="enf-change-patient" onClick={() => setBuscando(false)}>Volver a {paciente.nombre_completo}</button>}
              {!nuevoPaciente && <Boton onClick={() => { setNuevoPaciente(true); setErrorPaciente('') }}>+ Registrar paciente nuevo</Boton>}
            </div>
          </div>
          {nuevoPaciente
            ? <div className="enf-new-patient">
              <p>Registra la ficha para poder continuar con la admisión.</p>
              {errorPaciente && <p className="lab-form-error" role="alert">{errorPaciente}</p>}
              <FormularioPaciente datos={datosPaciente} pendiente={ocupado} onChange={cambiarDatosPaciente}
                onCancelar={() => { setNuevoPaciente(false); setErrorPaciente('') }} onGuardar={registrarPaciente} />
            </div>
            : <>
          <label className="enf-search-field">
            <svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
            <span className="sr-only">Buscar por nombre, documento, historia clínica o código</span>
            <input type="search" autoFocus value={entrada} onChange={(event) => setEntrada(event.target.value)}
              placeholder="Nombre, CI, historia clínica o código" aria-describedby="enf-search-hint" />
            {entrada && <button type="button" onClick={() => setEntrada('')} aria-label="Limpiar búsqueda">Limpiar</button>}
          </label>
          <p className="enf-search-hint" id="enf-search-hint">Escribe al menos dos caracteres para buscar.</p>

          {termino.length < 2
            ? <div className="enf-search-state">
              <span className="enf-search-state-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24"><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 4.5 4.5" /></svg>
              </span>
              <div><h3>Busca una ficha de paciente</h3><p>Los resultados aparecerán aquí mientras escribes.</p></div>
            </div>
            : esperandoBusqueda || pacientes.isPending
              ? <div className="enf-search-state" role="status">
                <span className="enf-search-spinner" aria-hidden="true" />
                <div><h3>Buscando pacientes</h3><p>Estamos consultando las fichas que coinciden.</p></div>
              </div>
              : pacientes.isError
                ? <div className="enf-search-state enf-search-state-error" role="alert">
                  <div><h3>No se pudo completar la búsqueda</h3><p>Comprueba la conexión e inténtalo de nuevo.</p></div>
                  <button type="button" className="enf-search-retry" onClick={() => pacientes.refetch()}>Reintentar</button>
                </div>
                : !pacientes.data?.items.length
                  ? <div className="enf-search-state">
                    <div><h3>No encontramos coincidencias</h3><p>Revisa los datos o registra una ficha nueva para continuar.</p></div>
                  </div>
                  : <>
                    <div className="enf-search-results-heading">
                      <div><h3>Resultados <span>{pacientes.data.total}</span></h3><p>Coincidencias para <strong>“{buscar}”</strong></p></div>
                    </div>
                    <ul className="enf-patient-results" aria-label="Pacientes encontrados">
                      {pacientes.data.items.map((item) => {
                        const iniciales = item.nombre_completo.trim().split(/\s+/).slice(0, 2).map((parte) => parte[0]).join('').toUpperCase()
                        return <li className="enf-patient-result" key={item.id}>
                          <div className="enf-result-person">
                            <span className="enf-result-avatar" aria-hidden="true">{iniciales}</span>
                            <div><h3>{item.nombre_completo}</h3><p>{item.numero_documento || 'Sin documento registrado'}</p></div>
                          </div>
                          <dl className="enf-result-data">
                            <div><dt>Historia clínica</dt><dd>{item.historia_clinica || 'No registrada'}</dd></div>
                            <div><dt>Código</dt><dd>{item.codigo_paciente}</dd></div>
                            <div><dt>Edad · sexo</dt><dd>{edadTexto(item.fecha_nacimiento)} · {item.sexo ? nombreSexo(item.sexo) : 'No registrado'}</dd></div>
                          </dl>
                          <button type="button" className="enf-result-action" onClick={() => elegirPaciente(item)}>
                            Seleccionar <span aria-hidden="true">→</span>
                          </button>
                        </li>
                      })}
                    </ul>
                    {pacientes.data.total > pacientes.data.limite && <div className="enf-search-pagination">
                      <span>Página {pagina} de {Math.max(1, Math.ceil(pacientes.data.total / pacientes.data.limite))}</span>
                      <div>
                        <button type="button" disabled={pagina === 1} onClick={() => setPagina((valor) => valor - 1)}>Anterior</button>
                        <button type="button" disabled={pagina * pacientes.data.limite >= pacientes.data.total} onClick={() => setPagina((valor) => valor + 1)}>Siguiente</button>
                      </div>
                    </div>}
                  </>}
            </>}
        </section>}

      {paciente && !buscando && <>
        <nav className="enf-tabs" role="tablist" aria-label="Secciones del paciente">
          <button type="button" role="tab" aria-selected={pantalla === 'admision'} className={pantalla === 'admision' ? 'active' : ''} onClick={() => setPantalla('admision')}>Nueva admisión</button>
          <button type="button" role="tab" aria-selected={pantalla === 'registros'} className={pantalla === 'registros' ? 'active' : ''} onClick={() => setPantalla('registros')}>Registros{registros.data?.length > 0 && <span className="enf-tab-count" aria-label={`${registros.data.length} registros`}>{registros.data.length}</span>}</button>
          <button type="button" role="tab" aria-selected={pantalla === 'recetas'} className={pantalla === 'recetas' ? 'active' : ''} onClick={() => setPantalla('recetas')}>
            Recetas recibidas{totalRecetas > 0 && <span className="enf-tab-count" aria-label={`${totalRecetas} recetas`}>{totalRecetas}</span>}
          </button>
        </nav>
        {pantalla === 'recetas' ? <RecetasRecibidas pacienteId={paciente.id} paciente={paciente} /> : pantalla === 'registros'
          ? <section className="enf-panel">
              <div className="enf-panel-heading"><h2>Registros de enfermería</h2><span>Borradores y registros publicados de este paciente.</span></div>
              {registros.isPending && <p role="status" className="enf-message">Cargando registros…</p>}
              {registros.isError && <p role="alert" className="enf-message">No se pudieron cargar los registros.</p>}
              {registros.data?.length === 0 && <p className="enf-message">Aún no hay registros de esta cuenta para el paciente.</p>}
              {registros.data?.length > 0 && <div className="enf-history-list">
                {registros.data.map((registro) => <RegistroResumen key={registro.id} registro={registro} ocupado={ocupado}
                  editando={edicion?.id === registro.id} onAbrir={(item) => navigate(`/enfermeria/pacientes/${paciente.id}/registros/${item.id}/informe`,
                    { state: { paciente, registro: item, pantalla: 'registros' } })} />)}
              </div>}
            </section>
          : <>
          <section className="enf-panel" ref={panelFormulario}>
            <div className="enf-panel-heading"><h2>{edicion ? 'Editar borrador' : 'Nueva admisión'}</h2><span>Los campos no medidos pueden dejarse vacíos. Enter pasa al siguiente.</span></div>
            {edicion && <p className="enf-editing-banner">Editando el borrador del {fechaHora(edicion.creado_en)}. Al guardar se reemplazan sus datos.</p>}
            <FormularioAdmision pacienteId={paciente.id} form={form} edad={edad} editando={Boolean(edicion)} ocupado={ocupado || iaBloqueada} error={error}
              hayErrores={erroresForm.length > 0} onCambiar={cambiarCampo} onGuardar={guardar}
              onCancelarEdicion={() => { limpiarFormulario(); setError('') }}
              onEstadoIA={({ bloqueado }) => setIaBloqueada(bloqueado)} />
          </section>
        </>}
      </>}
    </div>

    {confirmacion && <ConfirmarAccion titulo="Publicar registro de enfermería" textoConfirmar="Publicar para el médico"
      pendiente={ocupado} onCancelar={() => setConfirmacion(null)}
      onConfirmar={() => (confirmacion.origen === 'registro' ? publicarBorrador(confirmacion.registro) : ejecutarGuardado(true))}>
      <p>Paciente: <strong>{paciente?.nombre_completo}</strong>. Una vez publicado, el equipo médico lo verá y <strong>ya no se podrá editar</strong>.</p>
      <ResumenValores lineas={resumenConfirmacion} />
    </ConfirmarAccion>}

    {mostrarDescarte && <ConfirmarAccion titulo="Hay datos sin guardar" peligro
      textoConfirmar={descarte?.tipo === 'salir' ? 'Descartar y cerrar sesión' : descarte?.tipo === 'paciente' ? 'Descartar y cambiar de paciente' : 'Descartar y salir'}
      textoCancelar="Seguir editando" onCancelar={cancelarDescarte} onConfirmar={confirmarDescarte}>
      <p>La admisión{paciente ? <> de <strong>{paciente.nombre_completo}</strong></> : null} tiene datos que todavía no se guardaron. Si continúas, se perderán.</p>
      <p>Para conservarlos, vuelve y usa <strong>Guardar borrador</strong>.</p>
    </ConfirmarAccion>}
  </main>
}
