import ImagenEcografia from './ImagenEcografia.jsx'
import { edadEnEstudio } from '../informe.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'

/** Documento de lectura e impresión, separado del formulario de registro. */
export default function InformeEcografiaDocumento({ estudio, datos, guardados, archivos, publicado, documentoRef }) {
  const imagenes = guardados.filter(a => a.mime_type.startsWith('image/'))
  const organos = estudio.organos || []
  return (
      <article className="lab-report-document eco-documento" ref={documentoRef}>
        <header className="eco-cabecera"><div><strong>CENTRO DE SALUD INTEGRAL SARCOBAMBA</strong><p>COCHABAMBA · CERCADO</p></div><strong>SERVICIO DE ECOGRAFÍA</strong></header>
        {!publicado && <p className="eco-borrador">BORRADOR · PENDIENTE DE REVISIÓN Y PUBLICACIÓN</p>}
        <dl className="eco-identidad"><div><dt>Nombre:</dt><dd>{estudio.paciente_nombre}</dd></div><div><dt>Registro:</dt><dd>{estudio.codigo_paciente || 'No registrado'}</dd></div><div><dt>Fecha del estudio:</dt><dd>{formatearFecha(datos.fecha_estudio)}</dd></div><div><dt>Historia clínica:</dt><dd>{estudio.historia_clinica || 'No registrada'}</dd></div><div><dt>Establecimiento solicitante:</dt><dd>{datos.establecimiento || 'No registrado'}</dd></div><div><dt>Médico solicitante:</dt><dd>{estudio.medico_solicitante || 'No registrado'}</dd></div></dl>
        <p>Edad a la fecha del estudio: {edadEnEstudio(estudio.fecha_nacimiento, datos.fecha_estudio)}</p>
        <h2 className="eco-titulo">{estudio.tipo_estudio_nombre}</h2>
        {datos.zona && <p><strong>ZONA ESTUDIADA: </strong>{datos.zona}</p>}
        {organos.map(o => <p className="eco-hallazgo" key={o}><strong>{o.toLocaleUpperCase('es')}: </strong>{datos.evaluaciones[o] || 'Pendiente de registrar.'}</p>)}
        {datos.observaciones && <p className="eco-hallazgo"><strong>OBSERVACIONES: </strong>{datos.observaciones}</p>}
        <section className="eco-conclusion"><h3>CONCLUSIÓN</h3><p>{datos.conclusion || 'Pendiente de registrar.'}</p></section>
        <footer className="lab-report-signature"><div><span /><p>Firma y sello del profesional responsable</p></div><p>{estudio.referencia_estudio} · {publicado ? 'Publicado' : 'Borrador'}</p></footer>
        {(imagenes.length > 0 || archivos.some(a => a.type.startsWith('image/'))) && <section className="eco-laminas"><h3>IMÁGENES DEL ESTUDIO</h3><p>{estudio.paciente_nombre} · {estudio.referencia_estudio}</p><div className="eco-galeria">{imagenes.map(a => <ImagenEcografia key={a.id} archivo={a} />)}{archivos.filter(a => a.type.startsWith('image/')).map((a, i) => <ImagenEcografia key={`nuevo-${i}`} archivo={a} local />)}</div></section>}
        {guardados.some(a => !a.mime_type.startsWith('image/')) && <p>Otros adjuntos: {guardados.filter(a => !a.mime_type.startsWith('image/')).map(a => a.nombre_original).join(', ')}. Se conservan como archivos; no se incrustan en las láminas.</p>}
      </article>
  )
}
