import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { obtenerCatalogoImagenes, solicitarEcografia } from '../api/consultasApi.js'

/** El medico pide la ecografia desde la ficha del paciente. */
export default function SolicitarEcografia({ pacienteId, usuario }) {
  const [abierto, setAbierto] = useState(false)
  const [seleccion, setSeleccion] = useState([])
  const [estado, setEstado] = useState('')

  const catalogo = useQuery({
    queryKey: ['consultas', 'catalogo-imagenes'],
    queryFn: obtenerCatalogoImagenes,
    enabled: abierto,
  })

  function alternar(id) {
    setSeleccion((actual) => (actual.includes(id)
      ? actual.filter((valor) => valor !== id)
      : [...actual, id]))
  }

  async function enviar(evento) {
    evento.preventDefault()
    if (!seleccion.length) {
      setEstado('Elige al menos un estudio de ecografía.')
      return
    }
    setEstado('Enviando la solicitud…')
    try {
      await solicitarEcografia(pacienteId, seleccion, usuario.identificador_acceso)
      setEstado('Solicitud enviada al servicio de imagen.')
      setSeleccion([])
      setAbierto(false)
    } catch {
      setEstado('No se pudo enviar la solicitud. Inténtalo de nuevo.')
    }
  }

  if (!abierto) {
    return (
      <button type="button" className="med-button-link" onClick={() => setAbierto(true)}>
        + Solicitar ecografía
      </button>
    )
  }

  return (
    <form className="med-panel med-eco-form" onSubmit={enviar}>
      <div className="med-panel-header"><h2>Solicitar ecografía</h2><span>El radiólogo la recibirá en su bandeja</span></div>
      {catalogo.isPending && <p className="med-message">Cargando estudios disponibles…</p>}
      {catalogo.isError && <p role="alert" className="med-message">No se pudo cargar el catálogo de ecografías.</p>}
      {catalogo.data?.length === 0 && <p className="med-message">El servicio de imagen no tiene estudios configurados.</p>}
      {catalogo.data?.map((estudio) => (
        <label key={estudio.id} className="med-eco-opcion">
          <input
            type="checkbox"
            checked={seleccion.includes(estudio.id)}
            onChange={() => alternar(estudio.id)}
          />
          {estudio.nombre}
        </label>
      ))}
      {estado && <p className="med-message" role="status">{estado}</p>}
      <div className="med-eco-acciones">
        <button type="submit" className="primary-button" disabled={!seleccion.length}>Enviar solicitud</button>
        <button type="button" className="med-button-link" onClick={() => setAbierto(false)}>Cancelar</button>
      </div>
    </form>
  )
}
