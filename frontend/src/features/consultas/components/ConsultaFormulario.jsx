import { useEffect, useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useBlocker, useNavigate } from 'react-router-dom'
import { crearConsulta } from '../api/consultasApi.js'
import { usePaciente } from '../hooks/useConsultas.js'
import { IdentidadPaciente } from './PacienteFicha.jsx'
import { calcularImc, confirmarSalida, formularioAPayload, grupos } from '../utils/formulario.js'

const inicial = Object.fromEntries(grupos.flatMap(grupo => grupo.campos.map(([campo]) => [campo, ''])))

export default function ConsultaFormulario({ id, usuario }) {
  const paciente = usePaciente(id)
  const navegar = useNavigate()
  const cache = useQueryClient()
  const [form, setForm] = useState(inicial)
  const [sucio, setSucio] = useState(false)
  const [error, setError] = useState('')
  const clave = useRef(crypto.randomUUID())
  const guardado = useRef(false)
  const envio = useRef(false)
  const blocker = useBlocker(() => sucio && !guardado.current)
  const mutation = useMutation({ mutationFn: crearConsulta, onSuccess: async (detalle) => {
    guardado.current = true
    await cache.invalidateQueries({ queryKey: ['consultas', 'historial', id] })
    navegar(`/consultas/${detalle.id}`, { replace: true, state: { guardada: true } })
  }, onError: (err) => {
    envio.current = false
    const detalle = err.response?.data?.detail
    setError(typeof detalle === 'string' ? detalle : 'No se pudo guardar la consulta. Revisa los datos e inténtalo de nuevo.')
  } })

  useEffect(() => {
    const advertir = (evento) => {
      if (!sucio || guardado.current) return
      evento.preventDefault()
      evento.returnValue = ''
    }
    window.addEventListener('beforeunload', advertir)
    return () => window.removeEventListener('beforeunload', advertir)
  }, [sucio])

  useEffect(() => {
    if (blocker.state !== 'blocked') return
    if (confirmarSalida(true, mensaje => window.confirm(mensaje))) blocker.proceed()
    else blocker.reset()
  }, [blocker])

  useEffect(() => {
    function interceptarCierre(evento) {
      if (!evento.target.closest?.('.med-signout') || !sucio || guardado.current) return
      if (confirmarSalida(true, mensaje => window.confirm(mensaje))) guardado.current = true
      else { evento.preventDefault(); evento.stopPropagation() }
    }
    document.addEventListener('click', interceptarCierre, true)
    return () => document.removeEventListener('click', interceptarCierre, true)
  }, [sucio])

  function cambiar(campo, valor) {
    setForm(actual => ({ ...actual, [campo]: valor }))
    setSucio(true)
    setError('')
  }

  function salir() {
    navegar(`/consultas/pacientes/${id}`)
  }

  function enviar(evento) {
    evento.preventDefault()
    if (envio.current || mutation.isPending) return
    if (!form.motivo_consulta.trim() || !form.diagnostico_principal.trim()) {
      setError('Completa el motivo de consulta y el diagnóstico principal.')
      return
    }
    if (!window.confirm('¿Confirmas finalizar esta consulta? Después no podrás editarla.')) return
    envio.current = true
    mutation.mutate(formularioAPayload(form, id, clave.current))
  }

  if (paciente.isPending) return <p role="status">Cargando paciente…</p>
  if (paciente.isError) return <p role="alert">No se pudo cargar el paciente. No registres la consulta hasta confirmar su identidad.</p>
  const imc = calcularImc(form.peso_kg, form.talla_cm)
  return <>
    <div className="med-heading"><div><p className="med-eyebrow">CONSULTA EXTERNA · SOAP</p><h1>Nueva consulta</h1><p>Confirma al paciente antes de ingresar información clínica.</p></div></div>
    <IdentidadPaciente paciente={paciente.data} />
    <div className="med-metadata"><span>Profesional: <strong>{usuario.identificador_acceso}</strong></span><span>Fecha y número de consulta asignados al guardar</span></div>
    <form onSubmit={enviar} className="med-panel med-form">
      {grupos.map((grupo, indice) => <fieldset key={grupo.titulo}><legend>{indice ? grupo.titulo : 'Signos vitales y antropometría'}</legend><div className="med-fields">{grupo.campos.map(([campo, etiqueta]) => <label key={campo}>{etiqueta}{grupo.numerico
        ? <input type="number" inputMode="decimal" step="any" min="0" max={campo === 'saturacion_oxigeno' ? '100' : undefined} value={form[campo]} onChange={e => cambiar(campo, e.target.value)} placeholder="No registrado" />
        : <textarea required={campo === 'motivo_consulta' || campo === 'diagnostico_principal'} rows={3} value={form[campo]} onChange={e => cambiar(campo, e.target.value)} />}</label>)}</div>{grupo.numerico && <p className="med-hint">IMC calculado: <strong>{imc ?? 'Pendiente'}</strong> · Deja vacías las mediciones no realizadas.</p>}</fieldset>)}
      {error && <p role="alert" className="med-error">{error}</p>}
      <div className="med-form-actions"><button type="button" onClick={salir}>Volver a ficha</button><button className="primary-button" type="submit" disabled={mutation.isPending}>{mutation.isPending ? 'Guardando…' : 'Finalizar y guardar consulta'}</button></div>
    </form>
  </>
}
