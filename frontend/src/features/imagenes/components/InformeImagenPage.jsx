import { useEffect, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import '../../laboratorio/pages/laboratorio.css'
import '../../laboratorio/pages/informe-solicitud.css'
import { estadoEstudioImagen, formatearTamano } from '../../consultas/utils/examenes.js'
import { useRef } from 'react'
import { Link, useParams } from 'react-router-dom'
import '../pages/imagenes.css'

function ImagenAdjunta({ archivo, obtenerArchivoImagen }) {
  const [url, setUrl] = useState('')
  const imagen = useQuery({
    queryKey: ['imagenes', 'informe', 'archivo', archivo.id],
    queryFn: () => obtenerArchivoImagen(archivo.id),
    enabled: archivo.mime_type.startsWith('image/'),
  })
  useEffect(() => {
    if (!imagen.data) return undefined
    const objectUrl = URL.createObjectURL(imagen.data)
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [imagen.data])

  if (!archivo.mime_type.startsWith('image/')) return null
  if (imagen.isError) return <p role="alert">No se pudo cargar {archivo.nombre_original}.</p>
  if (!url) return <p role="status">Cargando {archivo.nombre_original}…</p>
  return <figure className="img-informe-figura"><img src={url} alt={`Imagen del estudio: ${archivo.nombre_original}`} /><figcaption>{archivo.nombre_original}</figcaption></figure>
}

function EditorInforme({ estudio, usuario, logout, modalidad, api }) {
  const cache = useQueryClient()
  const rayosX = modalidad === 'rayos_x'
  const titulo = rayosX ? 'Rayos X' : 'Ecografía'
  const rutaBandeja = rayosX ? '/rayos-x/gestion' : '/ecografia'
  const [descripcion, setDescripcion] = useState(estudio.informe?.descripcion_texto || '')
  const [archivos, setArchivos] = useState([])
  const [mensaje, setMensaje] = useState('')
  const [enviando, setEnviando] = useState(false)
  const entrada = useRef(null)

  async function guardar(evento) {
    evento.preventDefault()
    setEnviando(true)
    setMensaje('')
    try {
      await api.subirInforme(estudio.estudio_id, descripcion, archivos)
      setArchivos([])
      if (entrada.current) entrada.current.value = ''
      setMensaje('Borrador guardado. Revisa el informe antes de publicarlo.')
      await cache.invalidateQueries({ queryKey: [modalidad, 'estudio', estudio.estudio_id] })
    } catch (error) {
      const codigo = error?.response?.status
      setMensaje(codigo === 415 ? 'Hay un archivo con un formato no admitido.' : codigo === 413 ? 'Un archivo supera el tamaño permitido.' : 'No se pudo guardar el informe. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  async function publicar() {
    setEnviando(true)
    setMensaje('')
    try {
      await api.publicarInforme(estudio.estudio_id)
      setMensaje('Estudio publicado: ya aparece en el historial del paciente.')
      await cache.invalidateQueries({ queryKey: [modalidad, 'estudio', estudio.estudio_id] })
      await cache.invalidateQueries({ queryKey: [modalidad, 'bandeja'] })
    } catch (error) {
      setMensaje(error?.response?.status === 409 ? 'El informe ya estaba publicado o no tiene contenido.' : 'No se pudo publicar. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  const publicado = estudio.estado === 'publicado'
  const imagenes = estudio.informe?.archivos?.filter(a => a.mime_type.startsWith('image/')) || []

  return <main className="lab-page img-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo={titulo} inicio={rutaBandeja} onLogout={logout} />
      <section className="lab-content lab-report-page">
        <div className="lab-report-controls"><Link className="lab-back-link" to={rutaBandeja}>← Volver a la bandeja de {titulo}</Link><button type="button" className="primary-button" onClick={() => window.print()}>Imprimir o guardar PDF</button></div>
        <form className="lab-report-document img-informe" onSubmit={guardar}>
          <header className="lab-report-header"><div><p className="lab-report-institution">SarcoSistema · Diagnóstico por imágenes</p><h1>Informe de {titulo}</h1></div><strong>{estudio.referencia_estudio}</strong></header>
          <dl className="lab-report-meta">
            <div><dt>Paciente</dt><dd>{estudio.paciente_nombre}</dd></div><div><dt>Estudio solicitado</dt><dd>{estudio.tipo_estudio_nombre}</dd></div>
            <div><dt>Referencia de solicitud</dt><dd>{estudio.referencia_solicitud}</dd></div><div><dt>Fecha de solicitud</dt><dd>{new Date(estudio.fecha_solicitud).toLocaleDateString('es-BO')}</dd></div>
            <div><dt>Estado</dt><dd>{estadoEstudioImagen(estudio.estado)}</dd></div>{estudio.informe && <div><dt>Versión del informe</dt><dd>{estudio.informe.numero_version}</dd></div>}
          </dl>
          <section className="lab-report-study img-informe-cuerpo">
            <div className="lab-report-study-title"><div><span>Resultado</span><h2>{estudio.tipo_estudio_nombre}</h2></div></div>
            <label className="img-informe-campo"><span>Descripción e impresión diagnóstica</span><textarea rows="8" value={descripcion} maxLength={8000} onChange={e => setDescripcion(e.target.value)} placeholder="Registra los hallazgos y la impresión del estudio." disabled={publicado} /></label>
          </section>
          <section className="img-informe-adjuntos">
            <h2>Imágenes y archivos del estudio</h2>
            {!publicado && <label className="img-informe-campo"><span>Adjuntar archivos</span><input ref={entrada} type="file" multiple accept="image/*,application/pdf,.dcm" onChange={e => setArchivos([...e.target.files])} /></label>}
            {archivos.length > 0 && <ul className="img-archivos">{archivos.map(file => <li key={file.name}>{file.name} · {formatearTamano(file.size)}</li>)}</ul>}
            {imagenes.length > 0 ? <div className="img-informe-imagenes">{imagenes.map(archivo => <ImagenAdjunta key={archivo.id} archivo={archivo} obtenerArchivoImagen={api.obtenerArchivoImagen} />)}</div> : <p className="lab-report-empty">No hay imágenes adjuntas al informe.</p>}
            {estudio.informe?.archivos?.filter(a => !a.mime_type.startsWith('image/')).map(a => <p className="img-meta" key={a.id}>{a.nombre_original} · {formatearTamano(a.tamano_bytes)} (vista previa no disponible)</p>)}
          </section>
          {publicado && <p className="lab-report-responsible">Informe publicado{estudio.informe?.fecha_hora_publicacion ? ` el ${new Date(estudio.informe.fecha_hora_publicacion).toLocaleString('es-BO')}` : ''}. Disponible en el historial del paciente.</p>}
          <footer className="lab-report-signature img-informe-firma"><div><span /><p>Firma y sello del profesional responsable</p></div><p>Documento generado por SarcoSistema</p></footer>
          {!publicado && <div className="img-informe-controles"><button type="submit" className="lab-secondary-button" disabled={enviando}>Guardar borrador</button><button type="button" className="primary-button" disabled={enviando || (!descripcion.trim() && !estudio.informe?.archivos?.length && !archivos.length)} onClick={publicar}>Publicar informe</button></div>}
          {mensaje && <p className="img-mensaje" role="status">{mensaje}</p>}
        </form>
      </section>
    </div>
  </main>
}

export default function InformeImagenPage({ usuario, logout, modalidad = 'ecografia', api }) {
  const { estudioId } = useParams()
  const detalle = useQuery({ queryKey: [modalidad, 'estudio', Number(estudioId)], queryFn: () => api.obtenerEstudio(estudioId) })
  if (detalle.isPending) return <main className="lab-page"><p className="img-mensaje">Cargando informe…</p></main>
  if (detalle.isError) return <main className="lab-page"><p role="alert" className="img-mensaje">No se pudo cargar el informe del estudio.</p><Link to={modalidad === 'rayos_x' ? '/rayos-x/gestion' : '/ecografia'}>Volver a la bandeja</Link></main>
  return <EditorInforme key={estudioId} estudio={detalle.data} usuario={usuario} logout={logout} modalidad={modalidad} api={api} />
}
