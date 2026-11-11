import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useLocation, useParams } from 'react-router-dom'
import { obtenerHistorial, obtenerPaciente } from '../api/consultasApi.js'
import { obtenerArchivoImagen } from '../../imagenes/api/imagenesApi.js'
import { fecha } from '../utils/paciente.js'
import '../../laboratorio/pages/laboratorio.css'
import '../../laboratorio/pages/informe-solicitud.css'
import '../../imagenes/pages/imagenes.css'

function ImagenAdjunta({ archivo }) {
  const [url, setUrl] = useState('')
  const imagen = useQuery({
    queryKey: ['consultas', 'ecografia', 'archivo', archivo.id],
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

export default function InformeEcografiaMedico() {
  const { pacienteId, estudioId } = useParams()
  const ubicacion = useLocation()
  const historial = useQuery({
    queryKey: ['consultas', 'historial', pacienteId, 'ecografia-informe'],
    queryFn: () => obtenerHistorial(pacienteId),
  })
  const paciente = useQuery({
    queryKey: ['consultas', 'paciente', pacienteId],
    queryFn: () => obtenerPaciente(pacienteId),
  })
  const estudio = historial.data?.estudios_imagen?.find(e => e.estudio_id === Number(estudioId))
  const rayosX = ubicacion.pathname.includes('/rayos-x/') || /radiograf|rayos x/i.test(estudio?.tipo_estudio_nombre || '')
  const seccionVolver = rayosX ? 'rayos_x' : 'imagenes'
  const titulo = rayosX ? 'Informe de Rayos X' : 'Informe de ecografía'

  if (historial.isPending || paciente.isPending) return <section className="lab-report-page"><p role="status">Cargando informe de imágenes…</p></section>
  if (historial.isError || paciente.isError || !estudio) return <section className="lab-report-page"><p role="alert" className="lab-report-error">No se pudo cargar el informe publicado para este paciente.</p><Link className="lab-back-link" to={`/consultas/pacientes/${pacienteId}?seccion=${seccionVolver}`}>Volver a {rayosX ? 'Rayos X' : 'ecografías'}</Link></section>

  const archivos = estudio.archivos || []
  const imagenes = archivos.filter(a => a.mime_type.startsWith('image/'))
  const otros = archivos.filter(a => !a.mime_type.startsWith('image/'))
  return <section className="lab-report-page">
    <div className="lab-report-controls"><Link className="lab-back-link" to={`/consultas/pacientes/${pacienteId}?seccion=${seccionVolver}`}>← Volver a {rayosX ? 'Rayos X' : 'ecografías'}</Link><button className="primary-button" type="button" onClick={() => window.print()}>Imprimir o guardar PDF</button></div>
    <article className="lab-report-document img-informe">
      <header className="lab-report-header"><div><p className="lab-report-institution">SarcoSistema · Diagnóstico por imágenes</p><h1>{titulo}</h1></div><strong>{estudio.referencia_estudio}</strong></header>
      <dl className="lab-report-meta">
        <div><dt>Paciente</dt><dd>{paciente.data.nombre_completo}</dd></div>
        <div><dt>Documento</dt><dd>{paciente.data.numero_documento || 'No registrado'}</dd></div>
        <div><dt>Estudio</dt><dd>{estudio.tipo_estudio_nombre}</dd></div>
        <div><dt>Fecha de solicitud</dt><dd>{fecha(estudio.fecha_solicitud)}</dd></div>
        <div><dt>Fecha de publicación</dt><dd>{fecha(estudio.fecha_publicacion)}</dd></div>
        <div><dt>Referencia</dt><dd>{estudio.referencia_estudio}</dd></div>
      </dl>
      <section className="lab-report-study img-informe-cuerpo">
        <div className="lab-report-study-title"><div><span>Resultado</span><h2>{estudio.tipo_estudio_nombre}</h2></div></div>
        {estudio.descripcion_texto ? <p className="img-medico-descripcion">{estudio.descripcion_texto}</p> : <p className="lab-report-empty">El informe no tiene texto registrado.</p>}
      </section>
      <section className="img-informe-adjuntos">
        <h2>Imágenes y archivos del estudio</h2>
        {imagenes.length ? <div className="img-informe-imagenes">{imagenes.map(archivo => <ImagenAdjunta key={archivo.id} archivo={archivo} />)}</div> : <p className="lab-report-empty">No hay imágenes adjuntas al informe.</p>}
        {otros.map(archivo => <p className="img-meta" key={archivo.id}>{archivo.nombre_original} · vista previa no disponible</p>)}
      </section>
      <footer className="lab-report-signature img-informe-firma"><div><span /><p>Firma y sello del profesional responsable</p></div><p>Documento publicado el {fecha(estudio.fecha_publicacion)} · SarcoSistema</p></footer>
    </article>
  </section>
}
