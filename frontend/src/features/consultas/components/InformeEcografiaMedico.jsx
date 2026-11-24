import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useLocation, useParams } from 'react-router-dom'
import { obtenerHistorial, obtenerPaciente } from '../api/consultasApi.js'
import { esImagenVisible, obtenerImagenVisible } from '../../ecografia/api/ecografiaApi.js'
import { fecha } from '../utils/paciente.js'
import { describirEdad } from '../../../shared/utils/edad.js'
import { partirTextoInforme } from '../../rayos_x/estudio/utils/informe.js'
import '../../laboratorio/pages/informe-solicitud.css'
import '../../ecografia/pages/informe-imagen.css'
import '../../ecografia/pages/ecografia.css'
import Boton, { BotonEnlace } from '../../../shared/ui/Boton.jsx'

const SALTO = String.fromCharCode(10)

function ImagenAdjunta({ archivo }) {
  const [url, setUrl] = useState('')
  const imagen = useQuery({
    queryKey: ['consultas', 'ecografia', 'archivo', archivo.id],
    queryFn: () => obtenerImagenVisible(archivo),
    enabled: esImagenVisible(archivo.mime_type),
  })
  useEffect(() => {
    if (!imagen.data) return undefined
    const objectUrl = URL.createObjectURL(imagen.data)
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [imagen.data])

  if (!esImagenVisible(archivo.mime_type)) return null
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
  const esTorax = rayosX && /t[oó]rax/i.test(estudio?.tipo_estudio_nombre || '')
  const seccionVolver = rayosX ? 'rayos_x' : 'imagenes'

  if (historial.isPending || paciente.isPending) return <section className="lab-report-page"><p role="status">Cargando informe de imágenes…</p></section>
  if (historial.isError || paciente.isError || !estudio) return <section className="lab-report-page"><p role="alert" className="lab-report-error">No se pudo cargar el informe publicado para este paciente.</p><Link className="lab-back-link" to={`/consultas/pacientes/${pacienteId}?seccion=${seccionVolver}`}>Volver a {rayosX ? 'Rayos X' : 'ecografías'}</Link></section>

  const archivos = estudio.archivos || []
  const imagenes = archivos.filter(a => esImagenVisible(a.mime_type))
  const otros = archivos.filter(a => !esImagenVisible(a.mime_type))
  // Ecografía con plantilla: se usan los datos estructurados, como en su propio documento.
  const eco = !rayosX && estudio.datos_ecografia ? estudio.datos_ecografia : null
  const secciones = partirTextoInforme(estudio.descripcion_texto || '')
  const conclusion = secciones.find(sec => /CONCLUSI/i.test(sec.titulo || ''))
  const cuerpo = secciones.filter(sec => sec !== conclusion)
  return <section className="lab-report-page">
    <div className="lab-report-controls"><Link className="lab-back-link" to={`/consultas/pacientes/${pacienteId}?seccion=${seccionVolver}`}>← Volver a {rayosX ? 'Rayos X' : 'ecografías'}</Link>{esTorax && <BotonEnlace variante="secundario" to={`/imagenes/rayos-x?estudio=${estudioId}`}>Abrir con asistente IA</BotonEnlace>}<Boton onClick={() => window.print()}>Imprimir o guardar PDF</Boton></div>
    <article className="lab-report-document eco-documento">
      <header className="eco-cabecera"><div><strong>CENTRO DE SALUD INTEGRAL SARCOBAMBA</strong><p>COCHABAMBA · CERCADO</p></div><strong>{rayosX ? 'SERVICIO DE RAYOS X' : 'SERVICIO DE ECOGRAFÍA'}</strong></header>
      <dl className="eco-identidad">
        <div><dt>Nombre:</dt><dd>{paciente.data.nombre_completo}</dd></div>
        <div><dt>Registro:</dt><dd>{paciente.data.codigo_paciente || 'No registrado'}</dd></div>
        <div><dt>Fecha del estudio:</dt><dd>{fecha(estudio.datos_ecografia?.fecha_estudio || estudio.fecha_solicitud)}</dd></div>
        <div><dt>Documento:</dt><dd>{paciente.data.numero_documento || 'No registrado'}</dd></div>
        <div><dt>Establecimiento solicitante:</dt><dd>{estudio.datos_ecografia?.establecimiento || 'C.S. Sarcobamba'}</dd></div>
        <div><dt>Publicado:</dt><dd>{fecha(estudio.fecha_publicacion)}</dd></div>
      </dl>
      {paciente.data.fecha_nacimiento && <p>Edad: {describirEdad(paciente.data.fecha_nacimiento)}</p>}
      <h2 className="eco-titulo">{estudio.tipo_estudio_nombre}</h2>
      {eco ? <>
          {eco.zona && <p className="eco-hallazgo"><strong>ZONA ESTUDIADA: </strong>{eco.zona}</p>}
          {Object.entries(eco.evaluaciones || {}).map(([organo, texto]) => <p className="eco-hallazgo" key={organo}><strong>{organo.toLocaleUpperCase('es')}: </strong>{texto || 'No registrado.'}</p>)}
          {eco.observaciones && <p className="eco-hallazgo"><strong>OBSERVACIONES: </strong>{eco.observaciones}</p>}
          <section className="eco-conclusion"><h3>CONCLUSIÓN</h3><p>{eco.conclusion || 'No registrada.'}</p></section>
        </>
        : <>
          {cuerpo.length || conclusion
            ? cuerpo.map((sec, i) => <p className="eco-hallazgo" key={`${sec.titulo}-${i}`}>{sec.titulo && <strong>{sec.titulo.replace(/:$/, '')}: </strong>}{sec.lineas.join(SALTO)}</p>)
            : <p className="lab-report-empty">El informe no tiene texto registrado.</p>}
          {conclusion && <section className="eco-conclusion"><h3>CONCLUSIÓN</h3><p>{conclusion.lineas.join(SALTO)}</p></section>}
        </>}
      <footer className="lab-report-signature"><div><span /><p>Firma y sello del profesional responsable</p></div><p>{estudio.referencia_estudio} · Publicado el {fecha(estudio.fecha_publicacion)}</p></footer>
      {(imagenes.length > 0 || otros.length > 0) && <section className="eco-laminas"><h3>IMÁGENES DEL ESTUDIO</h3><p>{paciente.data.nombre_completo} · {estudio.referencia_estudio}</p>
        {imagenes.length > 0 && <div className="eco-galeria">{imagenes.map(archivo => <ImagenAdjunta key={archivo.id} archivo={archivo} />)}</div>}
        {otros.map(archivo => <p className="img-meta" key={archivo.id}>{archivo.nombre_original} · vista previa no disponible</p>)}
      </section>}
    </article>
  </section>
}
