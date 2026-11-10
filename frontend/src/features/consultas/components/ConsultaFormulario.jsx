import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useBlocker, useNavigate } from 'react-router-dom'
import { crearConsulta } from '../api/consultasApi.js'
import { usePaciente } from '../hooks/useConsultas.js'
import { IdentidadPaciente } from './PacienteFicha.jsx'
import {
  calcularImc, conPresion, formularioAPayload, formularioInicial, grupos, sincronizarPresion,
  transferirEnfermeria,
} from '../utils/formulario.js'
import AsistenteClinico from './AsistenteClinico.jsx'
import AdmisionEnfermeria from './AdmisionEnfermeria.jsx'
import { aplicarSugerencia, deshacerSugerencia } from '../utils/sugerencias.js'
import { esDeHoy } from '../utils/paciente.js'
import { transportarConsultaDemo } from '../../ia/transporter/api/agenteLocalApi.js'
import { obtenerRegistrosPublicados } from '../../enfermeria/api/enfermeriaApi.js'
import CampoMedicion, { pasarAlSiguiente } from '../../enfermeria/components/CampoMedicion.jsx'
import { MEDICIONES, erroresDelFormulario } from '../../enfermeria/utils/signosVitales.js'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import { calcularEdad } from '../../../shared/utils/edad.js'

// Signos vitales: la presión se escribe en un campo ("120/80") en lugar de dos.
const CAMPOS_VITALES = ['peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca', 'frecuencia_respiratoria', 'presion', 'saturacion_oxigeno']
const OBLIGATORIOS = { motivo_consulta: 1, diagnostico_principal: 3 } // campo -> índice de su sección
const PRESION = new Set(['presion_sistolica', 'presion_diastolica'])
const etiquetaLimpia = (etiqueta) => etiqueta.replace(' *', '')
const etiquetas = Object.fromEntries(grupos.flatMap((grupo) => grupo.campos.map(([campo, etiqueta]) => [campo, etiquetaLimpia(etiqueta)])))
const tieneValor = (valor) => String(valor ?? '').trim() !== ''

export default function ConsultaFormulario({ id, usuario }) {
  return <FormularioPaciente key={id} id={id} usuario={usuario} />
}

/** Insignia de origen del dato: lo propuso la IA o lo trajo enfermería; siempre editable. */
function Origen({ tipo }) {
  if (tipo === 'ia') return <span className="med-ai-badge">Propuesta IA aceptada · editable</span>
  if (tipo === 'enfermeria') return <span className="med-ai-badge med-origin-nursing">De enfermería · editable</span>
  return null
}

function FormularioPaciente({ id, usuario }) {
  const paciente = usePaciente(id)
  const navegar = useNavigate()
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const [form, setForm] = useState(formularioInicial)
  const [seccionActiva, setSeccionActiva] = useState(0)
  const formRef = useRef(form)
  const versionesCampos = useRef({})
  const [origen, setOrigen] = useState({}) // campo -> 'ia' | 'enfermeria'
  const [estadoIA, setEstadoIA] = useState({ bloqueado: false, hayDatos: false })
  const [revisionesIA, setRevisionesIA] = useState([])
  const [sucio, setSucio] = useState(false)
  const [error, setError] = useState('')
  const [intentoGuardar, setIntentoGuardar] = useState(false)
  const [estadoTransporte, setEstadoTransporte] = useState('')
  const [transportando, setTransportando] = useState(false)
  const [transferencia, setTransferencia] = useState(null)
  const [confirmarFinal, setConfirmarFinal] = useState(false)
  const [cierrePendiente, setCierrePendiente] = useState(null) // botón "Cerrar sesión" interceptado
  const transporteEnCurso = useRef(false)
  const clave = useRef(crypto.randomUUID())
  const guardado = useRef(false)
  const envio = useRef(false)
  const autoTransferido = useRef(false)
  const blocker = useBlocker(() => sucio && !guardado.current)
  const admisiones = useQuery({
    queryKey: ['enfermeria', 'publicados', id],
    queryFn: () => obtenerRegistrosPublicados(id),
  })
  const mutation = useMutation({ mutationFn: crearConsulta, onSuccess: async (detalle) => {
    guardado.current = true
    await cache.invalidateQueries({ queryKey: ['consultas', 'historial', id] })
    notificar('Consulta finalizada y guardada.', 'exito')
    navegar(`/consultas/${detalle.id}`, { replace: true, state: { guardada: true } })
  }, onError: (err) => {
    envio.current = false
    setConfirmarFinal(false)
    const detalle = err.response?.data?.detail
    setError(typeof detalle === 'string' ? detalle : 'No se pudo guardar la consulta. Revisa los datos e inténtalo de nuevo.')
  } })

  const reemplazarForm = useCallback((nuevo) => {
    formRef.current = nuevo
    setForm(nuevo)
  }, [])

  /** Copia la admisión de enfermería a los campos vacíos. Manual: cuenta como cambio del médico. */
  const usarEnfermeria = useCallback((registro, manual) => {
    const resultado = transferirEnfermeria(formRef.current, registro)
    for (const campo of resultado.copiados) versionesCampos.current[campo] = (versionesCampos.current[campo] ?? 0) + 1
    reemplazarForm(resultado.form)
    setOrigen((actual) => ({ ...actual, ...Object.fromEntries(resultado.copiados.map((campo) => [campo, 'enfermeria'])) }))
    setTransferencia(resultado)
    if (manual && resultado.copiados.length) setSucio(true)
  }, [reemplazarForm])

  // Al abrir la consulta, si enfermería publicó hoy, sus datos ya aparecen cargados (y editables).
  useEffect(() => {
    const registro = admisiones.data?.[0]
    if (autoTransferido.current || !registro || !esDeHoy(registro.publicado_en)) return
    autoTransferido.current = true
    usarEnfermeria(registro, false)
  }, [admisiones.data, usarEnfermeria])

  const aplicarIA = useCallback((item, confirmado = false) => {
    const resultado = aplicarSugerencia(formRef.current, item, confirmado)
    if (resultado.aplicada) {
      const revision = (versionesCampos.current[item.campo] ?? 0) + 1
      versionesCampos.current[item.campo] = revision
      resultado.revisionAplicacion = revision
      reemplazarForm(PRESION.has(item.campo) ? sincronizarPresion(resultado.form) : resultado.form)
      setOrigen(actual => ({ ...actual, [item.campo]: 'ia' }))
      setSucio(true)
    }
    return resultado
  }, [reemplazarForm])

  const deshacerIA = useCallback((item) => {
    const nuevo = deshacerSugerencia(formRef.current, item, versionesCampos.current[item.campo])
    reemplazarForm(PRESION.has(item.campo) ? sincronizarPresion(nuevo) : nuevo)
    setOrigen(actual => ({ ...actual, [item.campo]: undefined }))
  }, [reemplazarForm])

  const registrarRevisionIA = useCallback((revision) => {
    setRevisionesIA(actual => [...actual.filter(r => r.propuesta_id !== revision.propuesta_id),
      ...(revision.campos_aceptados.length ? [revision] : [])])
  }, [])

  useEffect(() => { if (estadoIA.hayDatos) setSucio(true) }, [estadoIA.hayDatos])

  useEffect(() => {
    const advertir = (evento) => {
      if (!sucio || guardado.current) return
      evento.preventDefault()
      evento.returnValue = ''
    }
    window.addEventListener('beforeunload', advertir)
    return () => window.removeEventListener('beforeunload', advertir)
  }, [sucio])

  // "Cerrar sesión" está en el menú lateral: se intercepta el clic para preguntar con un diálogo propio.
  useEffect(() => {
    function interceptarCierre(evento) {
      const boton = evento.target.closest?.('.med-signout')
      if (!boton || !sucio || guardado.current) return
      evento.preventDefault(); evento.stopPropagation()
      setCierrePendiente(boton)
    }
    document.addEventListener('click', interceptarCierre, true)
    return () => document.removeEventListener('click', interceptarCierre, true)
  }, [sucio])

  function cambiar(campo, valor) {
    const afectados = campo === 'presion' ? ['presion_sistolica', 'presion_diastolica'] : [campo]
    for (const afectado of afectados) versionesCampos.current[afectado] = (versionesCampos.current[afectado] ?? 0) + 1
    reemplazarForm(campo === 'presion' ? conPresion(formRef.current, valor) : { ...formRef.current, [campo]: valor })
    setOrigen(actual => ({ ...actual, ...Object.fromEntries(afectados.map((afectado) => [afectado, undefined])) }))
    setSucio(true)
    setError('')
    setEstadoTransporte('')
  }

  /** Primer problema que impide guardar, con la sección donde corregirlo (null si se puede). */
  function problemaParaGuardar(actual) {
    const invalidos = erroresDelFormulario(actual)
    if (invalidos.length) return { seccion: 0, mensaje: 'Corrige los signos vitales marcados en rojo antes de continuar.' }
    for (const [campo, seccion] of Object.entries(OBLIGATORIOS)) {
      if (!tieneValor(actual[campo])) return { seccion, mensaje: 'Completa el motivo de consulta y el diagnóstico principal.' }
    }
    return null
  }

  async function transportar() {
    if (transporteEnCurso.current || transportando || estadoIA.bloqueado) return
    const problema = problemaParaGuardar(formRef.current)
    if (problema) {
      setSeccionActiva(problema.seccion)
      setError(`${problema.mensaje} Es necesario también para transportar.`)
      return
    }
    transporteEnCurso.current = true
    setTransportando(true)
    setError('')
    setEstadoTransporte('Conectando con el cuaderno destino…')
    try {
      const resultado = await transportarConsultaDemo({
        paciente_nombre: paciente.data.nombre_completo,
        codigo_paciente: paciente.data.codigo_paciente,
        historia_clinica: paciente.data.historia_clinica,
        profesional: usuario.identificador_acceso,
        datos: formRef.current,
      })
      setEstadoTransporte(`Consulta transportada para ${resultado.paciente}. El cuaderno destino la guardó.`)
    } catch (errorAgente) {
      setEstadoTransporte('')
      setError(errorAgente.message || 'No se pudo transportar la consulta. Comprueba que el agente y el cuaderno demo estén abiertos.')
    } finally {
      transporteEnCurso.current = false
      setTransportando(false)
    }
  }

  function enviar(evento) {
    evento.preventDefault()
    if (envio.current || mutation.isPending) return
    setIntentoGuardar(true)
    if (estadoIA.bloqueado) {
      setError('Termina o cancela el procesamiento y acepta o rechaza las propuestas pendientes antes de guardar.')
      return
    }
    const problema = problemaParaGuardar(form)
    if (problema) {
      setSeccionActiva(problema.seccion)
      setError(problema.mensaje)
      return
    }
    setError('')
    setConfirmarFinal(true)
  }

  function finalizar() {
    if (envio.current) return
    envio.current = true
    const payload = formularioAPayload(form, id, clave.current)
    if (revisionesIA.length) payload.revision_ia = revisionesIA
    mutation.mutate(payload)
  }

  function confirmarCierre() {
    guardado.current = true
    const boton = cierrePendiente
    setCierrePendiente(null)
    boton?.click()
  }

  if (paciente.isPending) return <p role="status">Cargando paciente…</p>
  if (paciente.isError) return <p role="alert">No se pudo cargar el paciente. No registres la consulta hasta confirmar su identidad.</p>
  const imc = calcularImc(form.peso_kg, form.talla_cm)
  const edad = calcularEdad(paciente.data.fecha_nacimiento)
  const origenDe = (campo) => (campo === 'presion' ? origen.presion_sistolica ?? origen.presion_diastolica : origen[campo])
  const estadoSeccion = (grupo, indice) => {
    const campos = indice === 0 ? CAMPOS_VITALES : grupo.campos.map(([campo]) => campo)
    const falta = Object.entries(OBLIGATORIOS).some(([campo, seccion]) => seccion === indice && !tieneValor(form[campo]))
    if (indice === 0 && erroresDelFormulario(form).length) return 'error'
    if (falta) return 'falta'
    return campos.some((campo) => tieneValor(form[campo])) ? 'completa' : 'vacia'
  }
  const resumenFinal = [
    ['Motivo de consulta', form.motivo_consulta], ['Diagnóstico principal', form.diagnostico_principal],
    ['Signos vitales', CAMPOS_VITALES.filter((campo) => tieneValor(form[campo])).map((campo) => `${campo === 'presion' ? 'PA' : MEDICIONES[campo].etiqueta} ${form[campo]}`).join(' · ')],
    ['Tratamiento', form.tratamiento], ['Medicamentos', form.medicamentos],
  ].filter(([, valor]) => tieneValor(valor))
  const camposConDatos = Object.keys(etiquetas).filter((campo) => tieneValor(form[campo])).length

  return <>
    <div className="med-heading"><div><p className="med-eyebrow">CONSULTA EXTERNA · SOAP</p><h1>Nueva consulta</h1></div></div>
    <IdentidadPaciente paciente={paciente.data} />
    <AdmisionEnfermeria consulta={admisiones} transferencia={transferencia} onUsar={() => usarEnfermeria(admisiones.data[0], true)} />
    <details className="med-assistant-wrap" open>
      <summary>Asistente de consulta <span>dictado o texto · revisas cada propuesta</span></summary>
      <AsistenteClinico key={id} pacienteId={id} valores={form} onAplicar={aplicarIA} onDeshacer={deshacerIA} onEstado={setEstadoIA} onRevision={registrarRevisionIA} />
    </details>
    <form onSubmit={enviar} onKeyDown={(evento) => { if (seccionActiva === 0) pasarAlSiguiente(evento) }} className="med-panel med-form" noValidate>
      <nav className="med-form-sections" role="tablist" aria-label="Secciones del formulario de consulta">
        {grupos.map((grupo, indice) => {
          const estado = estadoSeccion(grupo, indice)
          const marca = estado === 'completa' ? '✓' : estado === 'error' || (estado === 'falta' && intentoGuardar) ? '!' : estado === 'falta' ? '*' : ''
          return <button key={grupo.titulo} type="button" role="tab" aria-selected={seccionActiva === indice} aria-controls={`consulta-seccion-${indice}`} id={`consulta-tab-${indice}`}
            className={[seccionActiva === indice && 'active', `is-${estado}`, intentoGuardar && 'tras-intento'].filter(Boolean).join(' ')} onClick={() => setSeccionActiva(indice)}>
            {grupo.titulo}{marca && <span className="med-section-mark" aria-label={estado === 'completa' ? 'con datos' : estado === 'error' ? 'con errores' : 'falta un dato obligatorio'}>{marca}</span>}
          </button>
        })}
      </nav>
      <p className="med-form-section-count">Sección {seccionActiva + 1} de {grupos.length} · ✓ con datos · * obligatorio pendiente</p>
      {grupos.map((grupo, indice) => indice === seccionActiva && <fieldset key={grupo.titulo} role="tabpanel" id={`consulta-seccion-${indice}`} aria-labelledby={`consulta-tab-${indice}`}><legend>{grupo.titulo}</legend>
        {grupo.numerico
          ? <>
            <div className="enf-measurements">
              {CAMPOS_VITALES.map((campo) => <CampoMedicion key={campo} campo={campo} valor={form[campo]} edad={edad} deshabilitado={mutation.isPending} onCambiar={cambiar} insignia={<Origen tipo={origenDe(campo)} />} />)}
              <div className="enf-measure enf-imc" aria-live="polite"><span>IMC (calculado)</span><strong>{imc === null ? '—' : String(imc).replace('.', ',')}</strong></div>
            </div>
            <p className="med-hint">Deja vacías las mediciones no realizadas. Rojo: sobre lo habitual · azul: bajo lo habitual (no impide guardar). Enter pasa al siguiente campo.</p>
          </>
          : <div className="med-fields">{grupo.campos.map(([campo, etiqueta]) => <label key={campo} className={origen[campo] ? 'med-field-from-ai' : undefined}>{etiqueta}<Origen tipo={origen[campo]} />
            <textarea rows={3} value={form[campo]} onChange={e => cambiar(campo, e.target.value)} /></label>)}</div>}
      </fieldset>)}
      {error && <p role="alert" className="med-error">{error}</p>}
      {estadoTransporte && <p role="status" className="med-hint">{estadoTransporte}</p>}
      {estadoIA.bloqueado && <p className="med-hint">Revisa o rechaza las propuestas pendientes. La IA nunca guarda la consulta automáticamente.</p>}
      <div className="med-form-actions med-form-navigation">
        <button type="button" onClick={() => setSeccionActiva(actual => Math.max(0, actual - 1))} disabled={seccionActiva === 0}>Sección anterior</button>
        <button type="button" onClick={() => setSeccionActiva(actual => Math.min(grupos.length - 1, actual + 1))} disabled={seccionActiva === grupos.length - 1}>Siguiente sección</button>
        <span className="med-form-spacer" />
        <button type="button" onClick={() => navegar(`/consultas/pacientes/${id}`)}>Volver a ficha</button>
        <button className="primary-button" type="submit" disabled={mutation.isPending || transportando || estadoIA.bloqueado}>{mutation.isPending ? 'Guardando…' : 'Finalizar y guardar consulta…'}</button>
      </div>
      <details className="med-experimental">
        <summary>Herramientas experimentales</summary>
        <p className="med-hint">Envía una copia de esta consulta al cuaderno de demostración mediante el agente local. No guarda la consulta en SarcoSistema.</p>
        <button type="button" onClick={transportar} disabled={transportando || mutation.isPending || estadoIA.bloqueado}>{transportando ? 'Transportando…' : 'Transportar a demo destino'}</button>
      </details>
    </form>

    {confirmarFinal && <ConfirmarAccion titulo="Finalizar consulta" textoConfirmar="Finalizar y guardar" textoCancelar="Seguir editando"
      pendiente={mutation.isPending} onCancelar={() => setConfirmarFinal(false)} onConfirmar={finalizar}>
      <p>Paciente: <strong>{paciente.data.nombre_completo}</strong>. Una vez guardada, la consulta <strong>no se podrá editar</strong>.</p>
      <dl className="med-final-summary">{resumenFinal.map(([etiqueta, valor]) => <div key={etiqueta}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
      <p className="med-hint">{camposConDatos} campos con datos{revisionesIA.length ? ' · incluye propuestas de IA aceptadas por ti' : ''}{transferencia?.copiados.length ? ' · incluye datos de enfermería' : ''}.</p>
    </ConfirmarAccion>}

    {(blocker.state === 'blocked' || cierrePendiente) && <ConfirmarAccion titulo="La consulta no está guardada" peligro
      textoConfirmar={cierrePendiente ? 'Descartar y cerrar sesión' : 'Descartar y salir'} textoCancelar="Seguir editando"
      onCancelar={() => { if (blocker.state === 'blocked') blocker.reset(); setCierrePendiente(null) }}
      onConfirmar={() => { if (cierrePendiente) confirmarCierre(); else blocker.proceed() }}>
      <p>Si sales ahora se perderá lo que escribiste en esta consulta{estadoIA.hayDatos ? ' y la transcripción del dictado' : ''}.</p>
      <p>Para conservarla, vuelve y usa <strong>Finalizar y guardar consulta</strong>.</p>
    </ConfirmarAccion>}
  </>
}
