import { useEffect, useRef, useState } from 'react'
import { useBlocker } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  actualizarBorradorEnfermeria, buscarPacientesEnfermeria,
  guardarBorradorEnfermeria, obtenerRecetasRecibidasEnfermeria, obtenerRegistrosEnfermeria,
  publicarRegistroEnfermeria,
} from '../api/enfermeriaApi.js'
import '../../laboratorio/pages/laboratorio.css'
import './enfermeria.css'
import RecetasRecibidas from '../components/RecetasRecibidas.jsx'
import FormularioAdmision from '../components/FormularioAdmision.jsx'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import { nombreSexo } from '../../laboratorio/utils/catalogos.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import { calcularEdad, describirEdad } from '../../../shared/utils/edad.js'
import {
  FORMULARIO_VACIO, MEDICIONES, TEXTOS, cuerpoDesdeFormulario, erroresDelFormulario,
  formularioDesdeRegistro, formularioVacio, resumenDelFormulario,
} from '../utils/signosVitales.js'

const fechaHora = (value) => value ? new Date(value).toLocaleString('es-BO') : 'Sin fecha'
const etiquetasCampos = {
  ...Object.fromEntries(TEXTOS),
  ...Object.fromEntries(Object.entries(MEDICIONES).map(([campo, { etiqueta }]) => [campo, etiqueta])),
  presion_sistolica: 'Presión sistólica', presion_diastolica: 'Presión diastólica', dolor_escala: 'Dolor',
}
function mensajeErrorApi(error, porDefecto) {
  const detalle = error.response?.data?.detail
  if (Array.isArray(detalle)) return detalle.map((item) => {
    const campo = item.loc?.at(-1)
    const etiqueta = etiquetasCampos[campo]
    const mensaje = String(item.msg || 'Dato no válido').replace(/^Value error, /, '')
    return `${etiqueta ? `${etiqueta}: ` : ''}${mensaje}`
  }).join(' ')
  if (typeof detalle === 'string') return detalle
  return porDefecto
}
const edadTexto = (nacimiento) => describirEdad(nacimiento) || 'Edad no registrada'
const MENSAJE_PUBLICADO = 'Registro publicado. Ya está disponible en la ficha médica del paciente.'

function ResumenValores({ lineas }) {
  return <dl className="enf-summary">{lineas.map(({ campo, etiqueta, valor }) =>
    <div key={campo}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
}

function RegistroResumen({ registro, editando, onEditar, onPublicar, ocupado }) {
  return <article className={editando ? 'enf-record is-editing' : 'enf-record'}>
    <header><div><strong>{registro.estado === 'publicado' ? 'Publicado' : editando ? 'Borrador · en edición' : 'Borrador'}</strong>
      <span>{fechaHora(registro.publicado_en || registro.creado_en)}</span></div>
      {registro.estado === 'publicado' && <span className="enf-published">Visible para el médico</span>}</header>
    <ResumenValores lineas={resumenDelFormulario(formularioDesdeRegistro(registro))} />
    {registro.estado === 'borrador' && <div className="enf-actions">
      <button type="button" onClick={() => onEditar(registro)} disabled={ocupado || editando}>Editar borrador</button>
      <button type="button" className="primary-button" onClick={() => onPublicar(registro)} disabled={ocupado}>Publicar para el médico…</button>
    </div>}
  </article>
}

export default function EnfermeriaPage({ usuario, logout }) {
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const [entrada, setEntrada] = useState('')
  const [buscar, setBuscar] = useState('')
  const [pagina, setPagina] = useState(1)
  const [paciente, setPaciente] = useState(null)
  const [buscando, setBuscando] = useState(true)
  const [form, setForm] = useState(FORMULARIO_VACIO)
  const [edicion, setEdicion] = useState(null) // registro borrador que se está editando
  const [ocupado, setOcupado] = useState(false)
  const [error, setError] = useState('')
  const [pantalla, setPantalla] = useState('admision')
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
  const erroresForm = erroresDelFormulario(form)
  const edad = calcularEdad(paciente?.fecha_nacimiento)

  function cambiarCampo(campo, valor) {
    setForm((actual) => ({ ...actual, [campo]: valor }))
  }

  function limpiarFormulario() {
    setForm(FORMULARIO_VACIO); setEdicion(null)
  }

  function abrirPaciente(item) {
    setPaciente(item)
    setBuscando(false)
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
    if (ocupado || !paciente) return
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
        notificar(`Se guardó como borrador, pero no se pudo publicar: ${mensajeErrorApi(err, 'inténtalo desde la lista de registros.')}`, 'error')
      } else {
        setError(mensajeErrorApi(err, 'No se pudo guardar. Revisa los datos e inténtalo de nuevo.'))
      }
    } finally {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', paciente.id] })
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
      notificar(mensajeErrorApi(err, 'No se pudo publicar el registro.'), 'error')
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
    <LaboratorioTopbar usuario={usuario} titulo="Enfermería" inicio="/enfermeria" onLogout={salir} />
    <div className="enf-content">
      <div className="enf-heading"><div><p>ADMISIÓN Y VALORACIÓN INICIAL</p><h1>Registro de enfermería</h1><span>Captura datos referidos y mediciones. Revisa y publica para que el médico pueda consultarlos.</span></div></div>

      {paciente && !buscando
        ? <section className="enf-panel enf-patient-card">
          <div><p>PACIENTE SELECCIONADO</p><h2>{paciente.nombre_completo}</h2>
            <span>{edadTexto(paciente.fecha_nacimiento)} · {paciente.sexo ? nombreSexo(paciente.sexo) : 'Sexo no registrado'} · HC {paciente.historia_clinica || 'No registrada'} · {paciente.codigo_paciente} · {paciente.numero_documento || 'Sin documento'}</span></div>
          <button type="button" className="enf-change-patient" onClick={() => setBuscando(true)}>Cambiar paciente</button>
        </section>
        : <section className="enf-panel">
          <div className="enf-panel-heading"><h2>Buscar paciente</h2>
            {paciente && <button type="button" className="enf-change-patient" onClick={() => setBuscando(false)}>Volver a {paciente.nombre_completo}</button>}</div>
          <label className="enf-search">Nombre, documento, historia clínica o código
            <input type="search" autoFocus value={entrada} onChange={(event) => setEntrada(event.target.value)} placeholder="Escribe al menos dos caracteres" />
          </label>
          {buscar.length < 2 && <p className="enf-message">Escribe al menos dos caracteres para buscar.</p>}
          {pacientes.isPending && buscar.length >= 2 && <p role="status" className="enf-message">Buscando…</p>}
          {pacientes.isError && <p role="alert" className="enf-message">No se pudo buscar pacientes.</p>}
          {pacientes.data?.items.map((item) => <button type="button" className={`enf-patient-option ${paciente?.id === item.id ? 'enf-selected' : ''}`} key={item.id} onClick={() => elegirPaciente(item)}>
            <strong>{item.nombre_completo}</strong><span>HC {item.historia_clinica || 'No registrada'} · {item.codigo_paciente} · {edadTexto(item.fecha_nacimiento)}</span>
          </button>)}
          {pacientes.data?.total > pacientes.data?.limite && <div className="enf-pagination">
            <button type="button" disabled={pagina === 1} onClick={() => setPagina((valor) => valor - 1)}>Anterior</button>
            <span>Página {pagina} · {pacientes.data.total} resultados</span>
            <button type="button" disabled={pagina * pacientes.data.limite >= pacientes.data.total} onClick={() => setPagina((valor) => valor + 1)}>Siguiente</button>
          </div>}
          {buscar.length >= 2 && pacientes.data?.items.length === 0 && <p className="enf-message">No se encontraron pacientes.</p>}
        </section>}

      {paciente && !buscando && <>
        <nav className="enf-tabs" role="tablist" aria-label="Secciones del paciente">
          <button type="button" role="tab" aria-selected={pantalla === 'admision'} className={pantalla === 'admision' ? 'active' : ''} onClick={() => setPantalla('admision')}>Admisión</button>
          <button type="button" role="tab" aria-selected={pantalla === 'recetas'} className={pantalla === 'recetas' ? 'active' : ''} onClick={() => setPantalla('recetas')}>
            Recetas recibidas{totalRecetas > 0 && <span className="enf-tab-count" aria-label={`${totalRecetas} recetas`}>{totalRecetas}</span>}
          </button>
        </nav>
        {pantalla === 'recetas' ? <RecetasRecibidas pacienteId={paciente.id} /> : <>
          <section className="enf-panel" ref={panelFormulario}>
            <div className="enf-panel-heading"><h2>{edicion ? 'Editar borrador' : 'Nueva admisión'}</h2><span>Los campos no medidos pueden dejarse vacíos. Enter pasa al siguiente.</span></div>
            {edicion && <p className="enf-editing-banner">Editando el borrador del {fechaHora(edicion.creado_en)}. Al guardar se reemplazan sus datos.</p>}
            <FormularioAdmision form={form} edad={edad} editando={Boolean(edicion)} ocupado={ocupado} error={error}
              hayErrores={erroresForm.length > 0} onCambiar={cambiarCampo} onGuardar={guardar}
              onCancelarEdicion={() => { limpiarFormulario(); setError('') }} />
          </section>
          <section className="enf-panel"><div className="enf-panel-heading"><h2>Registros de enfermería</h2><span>Los borradores solo los ve su autora; publicados, también el médico.</span></div>
            {registros.isPending && <p role="status" className="enf-message">Cargando registros…</p>}
            {registros.isError && <p role="alert" className="enf-message">No se pudieron cargar los registros.</p>}
            {registros.data?.length === 0 && <p className="enf-message">Aún no hay registros de esta cuenta para el paciente.</p>}
            {registros.data?.map((registro) => <RegistroResumen key={registro.id} registro={registro} ocupado={ocupado}
              editando={edicion?.id === registro.id} onEditar={editarBorrador}
              onPublicar={(item) => setConfirmacion({ origen: 'registro', registro: item })} />)}
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
