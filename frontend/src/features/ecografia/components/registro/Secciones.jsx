import { formatearTamano } from '../../utils/archivos.js'

const ACEPTA = 'image/jpeg,image/png,image/webp,image/gif,image/tiff,application/pdf,.dcm'

function Seccion({ titulo, detalle, children }) {
  return <section className="lab-area-study eco-seccion">
    <header><h2>{titulo}</h2>{detalle && <small>{detalle}</small>}</header>
    {children}
  </section>
}

export function SeccionDatos({ datos, cambiar, requiereZona, deshabilitado }) {
  return <Seccion titulo="Datos del estudio">
    <div className="lab-form-grid eco-grid-3">
      <label>Fecha del estudio *<input type="date" required value={datos.fecha_estudio} disabled={deshabilitado} onChange={e => cambiar('fecha_estudio', e.target.value)} /></label>
      <label>Establecimiento solicitante<input maxLength={200} value={datos.establecimiento} disabled={deshabilitado} onChange={e => cambiar('establecimiento', e.target.value)} /></label>
      <label>Zona u órgano estudiado{requiereZona ? ' *' : ''}<input maxLength={300} value={datos.zona} disabled={deshabilitado} onChange={e => cambiar('zona', e.target.value)} placeholder="Zona y lateralidad cuando corresponda" /></label>
    </div>
  </Seccion>
}

export function SeccionHallazgos({ organos, evaluaciones, cambiarOrgano, deshabilitado }) {
  const hechos = organos.filter(o => evaluaciones[o]?.trim()).length
  return <Seccion titulo="Hallazgos por órgano" detalle={`${hechos} de ${organos.length} registrados`}>
    <p className="lab-form-hint">Describe lo observado con sus mediciones y unidades. Si una estructura no se evaluó o no se visualiza, indícalo.</p>
    <div className="lab-form-grid eco-organos">
      {organos.map(o => <label key={o} className={evaluaciones[o]?.trim() ? 'es-completo' : undefined}>
        <span>{o} *</span>
        <textarea rows={3} maxLength={2000} value={evaluaciones[o] || ''} disabled={deshabilitado} onChange={e => cambiarOrgano(o, e.target.value)} />
      </label>)}
    </div>
  </Seccion>
}

export function SeccionAdjuntos({ guardados, nuevos, maximo, onAgregar, onQuitarGuardado, onQuitarNuevo, deshabilitado }) {
  const total = guardados.length + nuevos.length
  return <Seccion titulo="Imágenes y adjuntos" detalle={`${total} de ${maximo}`}>
    <label className="lab-search-label eco-subir">Añadir imágenes o archivos
      <input type="file" multiple accept={ACEPTA} disabled={deshabilitado || total >= maximo} onChange={e => { onAgregar([...e.target.files]); e.target.value = '' }} />
    </label>
    <p className="lab-form-hint">Puedes elegir varios archivos y añadir más en otra selección. JPG, PNG, PDF o DICOM.</p>
    {total > 0 && <ul className="eco-adjuntos">
      {guardados.map(a => <li key={a.id}><span>{a.nombre_original} · {formatearTamano(a.tamano_bytes)}</span><small>Guardado</small>
        <button type="button" className="lab-secondary-button" disabled={deshabilitado} onClick={() => onQuitarGuardado(a.id)}>Quitar</button></li>)}
      {nuevos.map((a, i) => <li key={`${a.name}:${i}`}><span>{a.name} · {formatearTamano(a.size)}</span><small className="es-nuevo">Sin guardar</small>
        <button type="button" className="lab-secondary-button" disabled={deshabilitado} onClick={() => onQuitarNuevo(i)}>Quitar</button></li>)}
    </ul>}
  </Seccion>
}

export function SeccionCierre({ datos, cambiar, deshabilitado }) {
  return <Seccion titulo="Conclusión">
    <div className="lab-form-grid eco-cierre">
      <label>Conclusión del profesional *<textarea rows={4} maxLength={4000} value={datos.conclusion} disabled={deshabilitado} onChange={e => cambiar('conclusion', e.target.value)} placeholder="Conclusión que se incluirá en el informe" /></label>
      <label>Observaciones adicionales <small>(opcional)</small><textarea rows={4} maxLength={4000} value={datos.observaciones} disabled={deshabilitado} onChange={e => cambiar('observaciones', e.target.value)} /></label>
    </div>
  </Seccion>
}
