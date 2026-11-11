import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { obtenerCatalogoImagenes, solicitarEcografia } from '../../consultas/api/consultasApi.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'

/** El médico pide una o varias ecografías desde la ficha del paciente. */
export default function SolicitarEstudioImagen({ pacienteId, usuario, modalidad = 'ecografia' }) {
  const rayosX = modalidad === 'rayos_x'
  const nombreModalidad = rayosX ? 'Rayos X' : 'ecografía'
  const { notificar } = useNotificacion()
  const [abierto, setAbierto] = useState(false)
  const [seleccion, setSeleccion] = useState([])
  const [urgente, setUrgente] = useState(false)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  // Una clave por solicitud: si se reintenta el envío, el backend no la duplica.
  const clave = useRef(null)

  const catalogo = useQuery({
    queryKey: ['consultas', 'catalogo-imagenes', modalidad],
    queryFn: () => obtenerCatalogoImagenes(modalidad),
    enabled: abierto,
  })

  function abrir() {
    clave.current = crypto.randomUUID()
    setSeleccion([]); setUrgente(false); setError(''); setAbierto(true)
  }

  function alternar(id) {
    setSeleccion((actual) => (actual.includes(id) ? actual.filter((valor) => valor !== id) : [...actual, id]))
  }

  async function enviar(evento) {
    evento.preventDefault()
    if (!seleccion.length || enviando) return
    setEnviando(true); setError('')
    try {
      await solicitarEcografia(pacienteId, seleccion, usuario.identificador_acceso, {
        prioridad: urgente ? 'urgente' : 'sin_prioridad', claveIdempotencia: clave.current, modalidad,
      })
      notificar(`${seleccion.length} ${rayosX ? 'estudio(s) de Rayos X solicitado(s)' : seleccion.length === 1 ? 'ecografía solicitada' : 'ecografías solicitadas'}${urgente ? ' con prioridad urgente' : ''}. El servicio de imagen la recibió en su bandeja.`, 'exito')
      setAbierto(false)
    } catch (err) {
      const detalle = err.response?.data?.detail
      setError(typeof detalle === 'string' ? detalle : 'No se pudo enviar la solicitud. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  if (!abierto) {
    return <div className="med-eco-request-bar">
      <button type="button" className="med-secondary-button" onClick={abrir}>+ Solicitar {nombreModalidad}</button>
    </div>
  }

  const nombres = Object.fromEntries((catalogo.data ?? []).map((estudio) => [estudio.id, estudio.nombre]))
  return (
    <form className="med-panel med-eco-form" onSubmit={enviar}>
      <div className="med-panel-header">
        <div><h2>Solicitar {nombreModalidad}</h2><span>El servicio de imagen la recibirá en su bandeja.</span></div>
      </div>
      <div className="med-eco-form-body">
        <fieldset className="med-eco-group">
          <legend>Estudios <small>puedes elegir varios</small></legend>
          {catalogo.isPending && <p className="med-message">Cargando estudios disponibles…</p>}
          {catalogo.isError && <p role="alert" className="med-error">No se pudo cargar el catálogo de {nombreModalidad}.</p>}
          {catalogo.data?.length === 0 && <p className="med-message">El servicio de imagen no tiene estudios configurados.</p>}
          {catalogo.data?.length > 0 && <div className="med-eco-options">
            {catalogo.data.map((estudio) => <label key={estudio.id} className={`med-eco-option${seleccion.includes(estudio.id) ? ' is-selected' : ''}`}>
              <input type="checkbox" checked={seleccion.includes(estudio.id)} disabled={enviando} onChange={() => alternar(estudio.id)} />
              <span>{estudio.nombre}</span>
            </label>)}
          </div>}
        </fieldset>
        <fieldset className="med-eco-group">
          <legend>Prioridad</legend>
          <div className="med-eco-priority" role="radiogroup" aria-label="Prioridad">
            <label className={!urgente ? 'is-selected' : undefined}><input type="radio" name="prioridad-eco" checked={!urgente} disabled={enviando} onChange={() => setUrgente(false)} />Normal</label>
            <label className={urgente ? 'is-selected is-urgent' : undefined}><input type="radio" name="prioridad-eco" checked={urgente} disabled={enviando} onChange={() => setUrgente(true)} />Urgente</label>
          </div>
        </fieldset>
        {seleccion.length > 0 && <p className="med-hint">Seleccionadas: {seleccion.map((id) => nombres[id]).filter(Boolean).join(' · ')}</p>}
        {error && <p role="alert" className="med-error">{error}</p>}
      </div>
      <div className="med-eco-actions">
        <button type="button" className="med-secondary-button" disabled={enviando} onClick={() => setAbierto(false)}>Cancelar</button>
        <button type="submit" className="primary-button" disabled={!seleccion.length || enviando}>
          {enviando ? 'Enviando…' : `Enviar solicitud${seleccion.length ? ` (${seleccion.length})` : ''}`}
        </button>
      </div>
    </form>
  )
}
