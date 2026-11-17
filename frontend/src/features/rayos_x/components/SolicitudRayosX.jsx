import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { crearSolicitud, mensajeErrorApi, obtenerCatalogo } from '../api/radiologiaApi.js'
import SelectorEstudiosRx from '../gestion/components/SelectorEstudiosRx.jsx'
import { erroresDeEstudios, prepararEstudiosParaApi } from '../gestion/utils/solicitud.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import '../pages/rx-tokens.css'
import '../gestion/gestion.css'

/** El médico pide uno o varios estudios de Rayos X desde la ficha del paciente. */
export default function SolicitudRayosX({ pacienteId }) {
  const { notificar } = useNotificacion()
  const [abierto, setAbierto] = useState(false)
  const [estudios, setEstudios] = useState([])
  const [urgente, setUrgente] = useState(false)
  const [diagnostico, setDiagnostico] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [errores, setErrores] = useState([])
  // Una clave por solicitud: si se reintenta el envío, el backend no la duplica.
  const clave = useRef(null)
  const catalogo = useQuery({ queryKey: ['radiologia', 'catalogo'], queryFn: () => obtenerCatalogo(), enabled: abierto })

  function abrir() {
    clave.current = crypto.randomUUID()
    setEstudios([]); setUrgente(false); setDiagnostico(''); setErrores([]); setAbierto(true)
  }

  async function enviar(evento) {
    evento.preventDefault()
    if (enviando) return
    const problemas = erroresDeEstudios(catalogo.data, estudios)
    if (problemas.length) return setErrores(problemas)
    setEnviando(true); setErrores([])
    try {
      await crearSolicitud({
        paciente_id: Number(pacienteId), prioridad: urgente ? 'urgente' : 'sin_prioridad', procedencia: 'este_centro',
        diagnostico_principal: diagnostico.trim() || null, clave_idempotencia: clave.current,
        estudios: prepararEstudiosParaApi(estudios),
      })
      notificar(`${estudios.length} ${estudios.length === 1 ? 'estudio de Rayos X solicitado' : 'estudios de Rayos X solicitados'}${urgente ? ' con prioridad urgente' : ''}. El servicio los recibió en su lista de trabajo.`, 'exito')
      setAbierto(false)
    } catch (error) {
      setErrores([mensajeErrorApi(error, 'No se pudo enviar la solicitud. Inténtalo de nuevo.')])
    } finally {
      setEnviando(false)
    }
  }

  if (!abierto) {
    return <div className="med-eco-request-bar">
      <button type="button" className="med-secondary-button" onClick={abrir}>+ Solicitar Rayos X</button>
    </div>
  }

  return <form className="med-panel med-eco-form rx-page" onSubmit={enviar}>
    <div className="med-panel-header">
      <div><h2>Solicitar Rayos X</h2><span>Elige el estudio, el lado y las proyecciones que necesitas. El servicio de Rayos X los recibirá en su lista de trabajo.</span></div>
    </div>
    <div className="med-eco-form-body">
      {catalogo.isPending && <p className="med-message">Cargando estudios disponibles…</p>}
      {catalogo.isError && <p role="alert" className="med-error">No se pudo cargar el catálogo de Rayos X.</p>}
      {catalogo.data && <SelectorEstudiosRx catalogo={catalogo.data} valor={estudios} onChange={setEstudios} deshabilitado={enviando} />}
      <label className="med-eco-group">Diagnóstico o motivo general (opcional)
        <input value={diagnostico} maxLength={500} disabled={enviando} onChange={(e) => setDiagnostico(e.target.value)} />
      </label>
      <fieldset className="med-eco-group">
        <legend>Prioridad</legend>
        <div className="med-eco-priority" role="radiogroup" aria-label="Prioridad">
          <label className={!urgente ? 'is-selected' : undefined}><input type="radio" name="prioridad-rx" checked={!urgente} disabled={enviando} onChange={() => setUrgente(false)} />Normal</label>
          <label className={urgente ? 'is-selected is-urgent' : undefined}><input type="radio" name="prioridad-rx" checked={urgente} disabled={enviando} onChange={() => setUrgente(true)} />Urgente</label>
        </div>
      </fieldset>
      {errores.length > 0 && <ul role="alert" className="med-error">{errores.map((mensaje) => <li key={mensaje}>{mensaje}</li>)}</ul>}
    </div>
    <div className="med-eco-actions">
      <button type="button" className="med-secondary-button" disabled={enviando} onClick={() => setAbierto(false)}>Cancelar</button>
      <button type="submit" className="primary-button" disabled={!estudios.length || enviando}>
        {enviando ? 'Enviando…' : `Enviar solicitud${estudios.length ? ` (${estudios.length})` : ''}`}
      </button>
    </div>
  </form>
}
