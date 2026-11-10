import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useBandeja } from '../hooks/useBandeja.js'
import { obtenerEstudio, publicarInforme, subirInforme } from '../api/imagenesApi.js'
import { estadoEstudioImagen, formatearTamano } from '../../consultas/utils/examenes.js'
import './imagenes.css'

function TrabajarEstudio({ estudio, alTerminar }) {
  const [descripcion, setDescripcion] = useState('')
  const [archivos, setArchivos] = useState([])
  const [mensaje, setMensaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const entrada = useRef(null)

  async function guardar(evento) {
    evento.preventDefault()
    setEnviando(true)
    setMensaje('')
    try {
      await subirInforme(estudio.estudio_id, descripcion, archivos)
      setMensaje('Borrador guardado. Revisa las imágenes antes de publicar.')
    } catch (error) {
      const codigo = error?.response?.status
      setMensaje(codigo === 415
        ? 'Hay un archivo con un formato no admitido.'
        : codigo === 413
          ? 'Un archivo supera el tamaño permitido.'
          : 'No se pudo guardar el informe. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  async function publicar() {
    setEnviando(true)
    setMensaje('')
    try {
      await publicarInforme(estudio.estudio_id)
      setMensaje('Estudio publicado: ya aparece en el historial del paciente.')
      alTerminar()
    } catch (error) {
      const codigo = error?.response?.status
      setMensaje(codigo === 409
        ? 'El informe ya estaba publicado.'
        : 'No se pudo publicar. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form className="img-trabajo" onSubmit={guardar}>
      <h3>{estudio.tipo_estudio_nombre}</h3>
      <p className="img-meta">{estudio.paciente_nombre} · {estudio.referencia_estudio} · {estadoEstudioImagen(estudio.estado)}</p>
      <label>
        Informe
        <textarea
          rows="4"
          value={descripcion}
          maxLength={8000}
          onChange={(evento) => setDescripcion(evento.target.value)}
          placeholder="Descripción del estudio para el médico"
        />
      </label>
      <label>
        Imágenes del estudio
        <input
          ref={entrada}
          type="file"
          multiple
          accept="image/*,application/pdf,.dcm"
          onChange={(evento) => setArchivos([...evento.target.files])}
        />
      </label>
      {archivos.length > 0 && (
        <ul className="img-archivos">
          {archivos.map((archivo) => (
            <li key={archivo.name}>{archivo.name} · {formatearTamano(archivo.size)}</li>
          ))}
        </ul>
      )}
      {mensaje && <p className="img-mensaje" role="status">{mensaje}</p>}
      <div className="img-acciones">
        <button type="submit" className="primary-button" disabled={enviando}>Guardar borrador</button>
        <button type="button" className="med-button-link" disabled={enviando} onClick={publicar}>Publicar</button>
      </div>
    </form>
  )
}

export default function ImagenesPage({ usuario, logout }) {
  const bandeja = useBandeja()
  const [abierto, setAbierto] = useState(null)
  const detalle = useQuery({
    queryKey: ['imagenes', 'estudio', abierto],
    queryFn: () => obtenerEstudio(abierto),
    enabled: abierto !== null,
  })

  return (
    <main className="img-page">
      <aside className="img-sidebar">
        <div className="img-sidebar-heading"><strong>SarcoSistema</strong><span>IMAGEN</span></div>
        <nav aria-label="Módulo de imagen"><span className="img-nav-active">Bandeja de estudios</span></nav>
        <button className="img-signout" onClick={logout}>Cerrar sesión</button>
      </aside>
      <div className="img-main">
        <header className="img-topbar">
          <span>SERVICIO DE IMAGEN</span>
          <div><span className="img-session">● Sesión activa</span><strong>{usuario.identificador_acceso}</strong></div>
        </header>
        <section className="img-content">
          <div className="img-heading"><div><p className="img-eyebrow">ECOGRAFÍAS</p><h1>Bandeja de estudios</h1><p>Sube las imágenes y el informe; al publicar, el médico lo ve en el historial del paciente.</p></div></div>
          {bandeja.isPending && <p role="status" className="img-mensaje">Cargando bandeja…</p>}
          {bandeja.isError && <p role="alert" className="img-mensaje">No se pudo cargar la bandeja.</p>}
          {bandeja.data?.length === 0 && <p className="img-mensaje">No hay estudios pendientes.</p>}
          {bandeja.data?.length > 0 && (
            <table className="img-tabla">
              <thead><tr><th>Estudio</th><th>Paciente</th><th>Estado</th><th>Acción</th></tr></thead>
              <tbody>
                {bandeja.data.map((estudio) => (
                  <tr key={estudio.estudio_id}>
                    <td><strong>{estudio.tipo_estudio_nombre}</strong><small>{estudio.referencia_solicitud}</small></td>
                    <td>{estudio.paciente_nombre}</td>
                    <td>{estadoEstudioImagen(estudio.estado)}</td>
                    <td>
                      <button type="button" className="med-button-link" onClick={() => setAbierto(estudio.estudio_id)}>
                        Atender
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {abierto !== null && detalle.data && (
            <TrabajarEstudio estudio={detalle.data} alTerminar={() => { setAbierto(null); bandeja.refetch() }} />
          )}
        </section>
      </div>
    </main>
  )
}
