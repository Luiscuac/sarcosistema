import { useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import ConfirmarAccion from '../../laboratorio/components/ConfirmarAccion.jsx'
import InformeLibreEcografia from './InformeLibreEcografia.jsx'
import * as api from '../api/ecografiaApi.js'
import { agregarArchivos, iniciarDatos, pendientes } from '../informe.js'
import InformeEcografiaDocumento from './InformeEcografiaDocumento.jsx'
import { formatearTamano } from '../../consultas/utils/examenes.js'
import '../../laboratorio/pages/laboratorio.css'
import '../../laboratorio/pages/informe-solicitud.css'
import '../pages/informe-imagen.css'
import '../pages/ecografia.css'


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
  const [vista, setVista] = useState('registro')
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

  return <main className="lab-page img-page eco-page"><LaboratorioTopbar usuario={usuario} titulo="Ecografía" inicio="/ecografia" onLogout={logout} />
    <section className="lab-content lab-report-page">
      <div className="lab-report-controls"><Link className="lab-back-button" to="/ecografia" onClick={e => { if (cambio && !window.confirm('Hay cambios sin guardar. ¿Salir del informe?')) e.preventDefault() }}>← Bandeja de ecografías</Link><button className="lab-secondary-button" type="button" disabled={ocupado || cambio || !informe} onClick={imprimir}>Imprimir o guardar PDF</button></div>
      {!publicado && <div className="eco-editor-navigation">
        <div className="eco-editor-tabs" aria-label="Vistas del estudio">
          <button type="button" aria-pressed={vista === 'registro'} className={vista === 'registro' ? 'is-active' : ''} onClick={() => setVista('registro')}>Registrar estudio</button>
          <button type="button" aria-pressed={vista === 'informe'} className={vista === 'informe' ? 'is-active' : ''} onClick={() => setVista('informe')}>Vista previa del informe</button>
        </div>
        <span className="eco-save-state">{cambio ? 'Cambios sin guardar' : informe ? 'Borrador guardado' : 'Sin guardar'}</span>
      </div>}
      {!publicado && vista === 'informe' && <p className="eco-preview-notice">Vista previa del borrador. Revisa el documento y vuelve a «Registrar estudio» para guardar o publicar.</p>}
      {!publicado && <form className="eco-editor" hidden={vista !== 'registro'} onSubmit={guardar}>
        <div className="lab-title-row"><div><p className="lab-eyebrow">INFORME POR ÓRGANOS</p><h1>{estudio.tipo_estudio_nombre}</h1><p className="lab-intro">{estudio.paciente_nombre} · {estudio.codigo_paciente} · {estudio.referencia_estudio}</p></div><span className="lab-status">Borrador</span></div>
        <div className="eco-editor-progress"><div><strong>Hallazgos registrados</strong><span>{organos.filter(o => datos.evaluaciones[o]?.trim()).length} de {organos.length} estructuras</span></div><progress aria-label="Progreso de hallazgos" max={organos.length || 1} value={organos.filter(o => datos.evaluaciones[o]?.trim()).length} /></div>
        <nav className="eco-section-nav" aria-label="Secciones del registro"><a href="#eco-datos">1. Datos del estudio</a><a href="#eco-hallazgos">2. Hallazgos</a><a href="#eco-adjuntos">3. Imágenes</a><a href="#eco-cierre">4. Conclusión</a></nav>
        <p className="eco-ayuda">Registra lo observado y las mediciones con sus unidades. Si una estructura no se evaluó o no se visualiza, indícalo expresamente.</p>
        <fieldset id="eco-datos" disabled={ocupado}><legend>Datos del estudio</legend><div className="eco-datos">
          <label>Fecha del estudio<input type="date" required value={datos.fecha_estudio} onChange={e => cambiar('fecha_estudio', e.target.value)} /></label>
          <label>Establecimiento solicitante<input maxLength={200} value={datos.establecimiento} onChange={e => cambiar('establecimiento', e.target.value)} /></label>
          <label>Zona u órgano estudiado<input maxLength={300} value={datos.zona} onChange={e => cambiar('zona', e.target.value)} placeholder="Especifica la zona y lateralidad cuando corresponda" /></label>
        </div></fieldset>
        <fieldset id="eco-hallazgos" disabled={ocupado}><legend>Hallazgos por órgano · {organos.filter(o => datos.evaluaciones[o]?.trim()).length}/{organos.length}</legend><div className="eco-organos">{organos.map(o => <label key={o}>{o}<textarea rows={3} maxLength={2000} value={datos.evaluaciones[o] || ''} onChange={e => { setDatos(d => ({ ...d, evaluaciones: { ...d.evaluaciones, [o]: e.target.value } })); setCambio(true) }} placeholder="Descripción y mediciones registradas por el ecografista" /></label>)}</div></fieldset>

        <fieldset id="eco-adjuntos" disabled={ocupado}><legend>Imágenes y adjuntos · {guardados.length + archivos.length}/{estudio.max_archivos}</legend>
          <label>Añadir imágenes o archivos<input type="file" multiple accept="image/jpeg,image/png,image/webp,image/gif,image/tiff,application/pdf,.dcm" onChange={e => {
            try { setArchivos(agregarArchivos(archivos, [...e.target.files], estudio.max_archivos, guardados.length)); setCambio(true); setMensaje('') }
            catch (err) { setMensaje(err.message) }
            e.target.value = ''
          }} /></label><p className="eco-ayuda">Puedes seleccionar varios archivos y añadir más en otra selección. Los ya guardados se conservan.</p>
          <ul className="eco-adjuntos">{guardados.map(a => <li key={a.id}><span>{a.nombre_original} · {formatearTamano(a.tamano_bytes)} · Guardado</span><button type="button" className="lab-secondary-button" onClick={() => { setGuardados(lista => lista.filter(x => x.id !== a.id)); setCambio(true) }}>Quitar del borrador</button></li>)}{archivos.map((a, i) => <li key={`${a.name}:${i}`}><span>{a.name} · {formatearTamano(a.size)} · Sin guardar</span><button type="button" className="lab-secondary-button" onClick={() => { setArchivos(lista => lista.filter((_, n) => n !== i)); setCambio(true) }}>Quitar</button></li>)}</ul>
        </fieldset>
        <fieldset id="eco-cierre" disabled={ocupado}><legend>Cierre del informe</legend><label>Observaciones adicionales<textarea rows={3} maxLength={4000} value={datos.observaciones} onChange={e => cambiar('observaciones', e.target.value)} /></label><label>Conclusión del profesional<textarea rows={3} maxLength={4000} value={datos.conclusion} onChange={e => cambiar('conclusion', e.target.value)} placeholder="Escribe la conclusión que deseas incluir en el informe" /></label></fieldset>
        {faltantes.length > 0 && <p className="eco-ayuda">Para publicar falta completar: {faltantes.join(', ')}.</p>}
        <div className="eco-acciones"><button type="button" className="lab-secondary-button" onClick={() => setVista('informe')}>Vista previa</button><button className="lab-secondary-button" disabled={ocupado} type="submit">{ocupado ? 'Procesando…' : 'Guardar borrador'}</button><button className="primary-button" type="button" disabled={ocupado || cambio || !informe?.datos_ecografia || faltantes.length > 0} onClick={() => setConfirmar(true)}>Revisar y publicar</button></div>
        {cambio && <p className="eco-ayuda">Guarda los cambios para poder publicar o imprimir.</p>}
      </form>}
      {mensaje && <p className="eco-mensaje" role="status">{mensaje}</p>}
      <div className="eco-informe-vista" hidden={!publicado && vista !== 'informe'}>
        <InformeEcografiaDocumento estudio={estudio} datos={datos} guardados={guardados} archivos={archivos} publicado={publicado} documentoRef={documento} />
      </div>
    </section>
    {confirmar && <ConfirmarAccion titulo="Publicar informe de ecografía" textoConfirmar="Publicar informe" textoCancelar="Seguir revisando" pendiente={ocupado} onCancelar={() => setConfirmar(false)} onConfirmar={publicar}><p>Se publicará el informe de <strong>{estudio.paciente_nombre}</strong> con {guardados.length} adjuntos. El médico podrá consultarlo. Después de publicar no se podrá editar este informe.</p></ConfirmarAccion>}
  </main>
}

export default function EditorEcografia(props) {
  const { estudioId } = useParams()
  const consulta = useQuery({ queryKey: ['ecografia', 'estudio', Number(estudioId)], queryFn: () => api.obtenerEstudio(estudioId) })
  if (consulta.isPending) return <p className="img-mensaje" role="status">Cargando ecografía…</p>
  if (consulta.isError) return <p className="img-mensaje" role="alert">No se pudo cargar el estudio. <Link to="/ecografia">Volver a la bandeja</Link></p>
  if (!consulta.data.organos?.length || (consulta.data.informe?.estado === 'publicado' && !consulta.data.informe.datos_ecografia)) return <InformeLibreEcografia {...props} key={estudioId} estudio={consulta.data} />
  return <Editor {...props} key={estudioId} estudio={consulta.data} />
}
