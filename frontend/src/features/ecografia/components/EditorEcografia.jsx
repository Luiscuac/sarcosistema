import { useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'
import InformeImagenPage from '../../imagenes/components/InformeImagenPage.jsx'
import * as api from '../api/ecografiaApi.js'
import { agregarArchivos, iniciarDatos, pendientes, edadEnEstudio } from '../informe.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import { formatearTamano } from '../../consultas/utils/examenes.js'
import '../../laboratorio/pages/laboratorio.css'
import '../../laboratorio/pages/informe-solicitud.css'
import '../../imagenes/pages/imagenes.css'
import '../pages/ecografia.css'

function Imagen({ archivo, local = false }) {
  const [url, setUrl] = useState('')
  const consulta = useQuery({ queryKey: ['ecografia', 'adjunto', archivo.id], queryFn: () => api.obtenerArchivoImagen(archivo.id), enabled: !local })
  const blob = local ? archivo : consulta.data
  useEffect(() => {
    if (!blob) return undefined
    const u = URL.createObjectURL(blob); setUrl(u)
    return () => URL.revokeObjectURL(u)
  }, [blob])
  if (!url) return <p role={consulta.isError ? 'alert' : 'status'}>{consulta.isError ? 'No se pudo cargar la imagen.' : 'Cargando imagen…'}</p>
  return <figure className="eco-imagen"><img src={url} alt={archivo.nombre_original || archivo.name} /><figcaption>{archivo.nombre_original || archivo.name}</figcaption></figure>
}

function Editor({ estudio, usuario, logout }) {
  const cache = useQueryClient()
  const [datos, setDatos] = useState(() => iniciarDatos(estudio))
  const [archivos, setArchivos] = useState([])
  const [guardados, setGuardados] = useState(estudio.informe?.archivos || [])
  const [informe, setInforme] = useState(estudio.informe)
  const [cambio, setCambio] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [confirmar, setConfirmar] = useState(false)
  const documento = useRef(null)
  const publicado = informe?.estado === 'publicado'
  const organos = estudio.organos || []
  const faltantes = pendientes(datos, organos)
  const cambiar = (campo, valor) => { setDatos(d => ({ ...d, [campo]: valor })); setCambio(true) }

  async function guardar(e) {
    e.preventDefault(); setOcupado(true); setMensaje('')
    try {
      const nuevo = await api.subirInforme(estudio.estudio_id, '', archivos, { datos, conservar: guardados.map(a => a.id) })
      setInforme(nuevo); setGuardados(nuevo.archivos); setArchivos([]); setDatos(nuevo.datos_ecografia); setCambio(false)
      cache.setQueryData(['ecografia', 'estudio', estudio.estudio_id], { ...estudio, informe: nuevo })
      await cache.invalidateQueries({ queryKey: ['ecografia', 'bandeja'] })
      setMensaje('Borrador guardado con todos sus adjuntos.')
    } catch (err) { setMensaje(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo guardar el borrador.') }
    finally { setOcupado(false) }
  }

  async function publicar() {
    setOcupado(true)
    try {
      await api.publicarInforme(estudio.estudio_id)
      setInforme(i => ({ ...i, estado: 'publicado' })); setConfirmar(false)
      await cache.invalidateQueries({ queryKey: ['ecografia'] })
      setMensaje('Informe publicado. El médico ya puede consultarlo en la ficha del paciente.')
    } catch (err) { setMensaje(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'No se pudo publicar el informe.'); setConfirmar(false) }
    finally { setOcupado(false) }
  }

  async function imprimir() {
    const imagenes = [...documento.current.querySelectorAll('img')]
    if (documento.current.querySelector('[role="status"], [role="alert"]')) { setMensaje('Espera a que todas las imágenes estén disponibles antes de imprimir.'); return }
    try { await Promise.all(imagenes.map(img => img.decode())); window.print() }
    catch { setMensaje('Una imagen no pudo cargarse. Reintenta antes de imprimir.') }
  }

  const imagenes = guardados.filter(a => a.mime_type.startsWith('image/'))
  return <main className="lab-page img-page eco-page"><LaboratorioTopbar usuario={usuario} titulo="Ecografía" inicio="/ecografia" onLogout={logout} />
    <section className="lab-content lab-report-page">
      <div className="lab-report-controls"><Link className="lab-back-button" to="/ecografia" onClick={e => { if (cambio && !window.confirm('Hay cambios sin guardar. ¿Salir del informe?')) e.preventDefault() }}>← Bandeja de ecografías</Link><button className="lab-secondary-button" type="button" disabled={ocupado || cambio || !informe} onClick={imprimir}>Imprimir o guardar PDF</button></div>
      {!publicado && <form className="eco-editor" onSubmit={guardar}>
        <div className="lab-title-row"><div><p className="lab-eyebrow">INFORME POR ÓRGANOS</p><h1>{estudio.tipo_estudio_nombre}</h1><p className="lab-intro">{estudio.paciente_nombre} · {estudio.codigo_paciente} · {estudio.referencia_estudio}</p></div><span className="lab-status">Borrador</span></div>
        <p className="eco-ayuda">Registra lo observado y las mediciones con sus unidades. Si una estructura no se evaluó o no se visualiza, indícalo expresamente.</p>
        <fieldset disabled={ocupado}><legend>Datos del estudio</legend><div className="eco-datos">
          <label>Fecha del estudio<input type="date" required value={datos.fecha_estudio} onChange={e => cambiar('fecha_estudio', e.target.value)} /></label>
          <label>Establecimiento solicitante<input maxLength={200} value={datos.establecimiento} onChange={e => cambiar('establecimiento', e.target.value)} /></label>
          <label>Zona u órgano estudiado<input maxLength={300} value={datos.zona} onChange={e => cambiar('zona', e.target.value)} placeholder="Especifica la zona y lateralidad cuando corresponda" /></label>
        </div></fieldset>
        <fieldset disabled={ocupado}><legend>Hallazgos por órgano · {organos.filter(o => datos.evaluaciones[o]?.trim()).length}/{organos.length}</legend><div className="eco-organos">{organos.map(o => <label key={o}>{o}<textarea rows={3} maxLength={2000} value={datos.evaluaciones[o] || ''} onChange={e => { setDatos(d => ({ ...d, evaluaciones: { ...d.evaluaciones, [o]: e.target.value } })); setCambio(true) }} placeholder="Descripción y mediciones registradas por el ecografista" /></label>)}</div></fieldset>
        <fieldset disabled={ocupado}><legend>Cierre del informe</legend><label>Observaciones adicionales<textarea rows={3} maxLength={4000} value={datos.observaciones} onChange={e => cambiar('observaciones', e.target.value)} /></label><label>Conclusión del profesional<textarea rows={3} maxLength={4000} value={datos.conclusion} onChange={e => cambiar('conclusion', e.target.value)} placeholder="Escribe la conclusión que deseas incluir en el informe" /></label></fieldset>
        <fieldset disabled={ocupado}><legend>Imágenes y adjuntos · {guardados.length + archivos.length}/{estudio.max_archivos}</legend>
          <label>Añadir imágenes o archivos<input type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/tiff,application/pdf,.dcm" onChange={e => {
            try { setArchivos(agregarArchivos(archivos, [...e.target.files], estudio.max_archivos, guardados.length)); setCambio(true); setMensaje('') }
            catch (err) { setMensaje(err.message) }
            e.target.value = ''
          }} /></label><p className="eco-ayuda">Puedes seleccionar varios archivos y añadir más en otra selección. Los ya guardados se conservan.</p>
          <ul className="eco-adjuntos">{guardados.map(a => <li key={a.id}><span>{a.nombre_original} · {formatearTamano(a.tamano_bytes)} · Guardado</span><button type="button" className="lab-secondary-button" onClick={() => { setGuardados(lista => lista.filter(x => x.id !== a.id)); setCambio(true) }}>Quitar del borrador</button></li>)}{archivos.map((a, i) => <li key={`${a.name}:${i}`}><span>{a.name} · {formatearTamano(a.size)} · Sin guardar</span><button type="button" className="lab-secondary-button" onClick={() => { setArchivos(lista => lista.filter((_, n) => n !== i)); setCambio(true) }}>Quitar</button></li>)}</ul>
        </fieldset>
        {faltantes.length > 0 && <p className="eco-ayuda">Para publicar falta completar: {faltantes.join(', ')}.</p>}
        <div className="eco-acciones"><button className="lab-secondary-button" disabled={ocupado} type="submit">{ocupado ? 'Procesando…' : 'Guardar borrador'}</button><button className="primary-button" type="button" disabled={ocupado || cambio || !informe?.datos_ecografia || faltantes.length > 0} onClick={() => setConfirmar(true)}>Revisar y publicar</button></div>
        {cambio && <p className="eco-ayuda">Guarda los cambios para poder publicar o imprimir.</p>}
      </form>}
      {mensaje && <p className="eco-mensaje" role="status">{mensaje}</p>}
      <article className="lab-report-document eco-documento" ref={documento}>
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
        {(imagenes.length > 0 || archivos.some(a => a.type.startsWith('image/'))) && <section className="eco-laminas"><h3>IMÁGENES DEL ESTUDIO</h3><p>{estudio.paciente_nombre} · {estudio.referencia_estudio}</p><div className="eco-galeria">{imagenes.map(a => <Imagen key={a.id} archivo={a} />)}{archivos.filter(a => a.type.startsWith('image/')).map((a, i) => <Imagen key={`nuevo-${i}`} archivo={a} local />)}</div></section>}
        {guardados.some(a => !a.mime_type.startsWith('image/')) && <p>Otros adjuntos: {guardados.filter(a => !a.mime_type.startsWith('image/')).map(a => a.nombre_original).join(', ')}. Se conservan como archivos; no se incrustan en las láminas.</p>}
      </article>
    </section>
    {confirmar && <ConfirmarAccion titulo="Publicar informe de ecografía" textoConfirmar="Publicar informe" textoCancelar="Seguir revisando" pendiente={ocupado} onCancelar={() => setConfirmar(false)} onConfirmar={publicar}><p>Se publicará el informe de <strong>{estudio.paciente_nombre}</strong> con {guardados.length} adjuntos. El médico podrá consultarlo. Después de publicar no se podrá editar este informe.</p></ConfirmarAccion>}
  </main>
}

export default function EditorEcografia(props) {
  const { estudioId } = useParams()
  const consulta = useQuery({ queryKey: ['ecografia', 'estudio', Number(estudioId)], queryFn: () => api.obtenerEstudio(estudioId) })
  if (consulta.isPending) return <p className="img-mensaje" role="status">Cargando ecografía…</p>
  if (consulta.isError) return <p className="img-mensaje" role="alert">No se pudo cargar el estudio. <Link to="/ecografia">Volver a la bandeja</Link></p>
  if (!consulta.data.organos?.length || (consulta.data.informe?.estado === 'publicado' && !consulta.data.informe.datos_ecografia)) return <InformeImagenPage {...props} modalidad="ecografia" api={api} />
  return <Editor {...props} key={estudioId} estudio={consulta.data} />
}
