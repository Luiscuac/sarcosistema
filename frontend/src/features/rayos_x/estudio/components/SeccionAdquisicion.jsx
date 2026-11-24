import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import ConfirmarAccion from '../../../../shared/ui/ConfirmarAccion.jsx'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import { adjuntarInformeExterno, asignarProyeccion, completarAdquisicion, descargarInformeExterno, guardarAdquisicion, pendientesDeError, retirarImagen, retirarInformeExterno, subirImagenes } from '../../compartido/api/radiologiaApi.js'
import GaleriaImagenes from './GaleriaImagenes.jsx'
import PanelImagenes from './PanelImagenes.jsx'
import ResumenAvance from '../../../../shared/ui/ResumenAvance.jsx'
import { resumenAdquisicion } from '../utils/flujo.js'
import { parametrosANumeros, tamanoLegible, validarArchivoImagen } from '../utils/informe.js'
import Boton from '../../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'

const VACIO = { proyecciones_realizadas: [], lateralidad_realizada: '', posicion_paciente: '', fecha_hora_adquisicion: '', operador_nombre: '', calidad: '', limitaciones: '', repeticiones: 0, motivo_repeticion: '', observaciones: '', parametros: {} }
const aLocal = iso => {
  if (!iso) return ''
  const fecha = new Date(iso); const dos = numero => String(numero).padStart(2, '0')
  return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}T${dos(fecha.getHours())}:${dos(fecha.getMinutes())}`
}

function ZonaCarga({ proyecciones, disabled, onSubir }) {
  const [items, setItems] = useState([])
  const agregar = lista => setItems(Array.from(lista).slice(0, 10).map(archivo => ({ archivo, proyeccion: '', error: validarArchivoImagen(archivo) })))
  const validos = items.length > 0 && items.every(item => !item.error)
  return <div className="rxe-carga">
    <label className="rxe-drop" onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!disabled) agregar(e.dataTransfer.files) }}>
      <span>Arrastra imágenes aquí o selecciona archivos JPG, PNG o DICOM</span>
      <input type="file" multiple accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png,application/dicom" disabled={disabled} onChange={e => agregar(e.target.files)} />
    </label>
    {items.map((item, i) => <div className="rxe-archivo" key={`${item.archivo.name}-${item.archivo.lastModified}`}>
      <span>{item.archivo.name}</span><small>{tamanoLegible(item.archivo.size)}</small>
      <label>Proyección<select value={item.proyeccion} disabled={disabled || Boolean(item.error)} onChange={e => setItems(actual => actual.map((x, n) => n === i ? { ...x, proyeccion: e.target.value } : x))}>
        <option value="">Sin asignar</option>{proyecciones.map(p => <option key={p.codigo} value={p.codigo}>{p.nombre}</option>)}
      </select></label>{item.error && <p className="lab-form-error" role="alert">{item.error}</p>}
    </div>)}
    {items.length > 0 && <Boton disabled={disabled || !validos}
      onClick={() => onSubir(items.map(x => x.archivo), items.map(x => x.proyeccion), () => setItems([]))}>Subir imágenes</Boton>}
  </div>
}

function InformesExternos({ estudioId, informes, editable, actualizar }) {
  const { notificar } = useNotificacion()
  const [abierto, setAbierto] = useState(informes.length > 0)
  const [archivo, setArchivo] = useState(null)
  const [campos, setCampos] = useState({ establecimiento: '', profesional: '', fecha_informe: '', observaciones: '' })
  const [retirar, setRetirar] = useState(null); const [motivo, setMotivo] = useState('')
  const adjuntar = useMutation({ mutationFn: () => adjuntarInformeExterno(estudioId, archivo, campos), onSuccess: dato => { actualizar(dato); setArchivo(null); setCampos({ establecimiento: '', profesional: '', fecha_informe: '', observaciones: '' }); notificar('Informe externo adjuntado.', 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const quitar = useMutation({ mutationFn: () => retirarInformeExterno(estudioId, retirar.id, motivo.trim()), onSuccess: dato => { actualizar(dato); setRetirar(null); setMotivo(''); notificar('Informe externo retirado.', 'exito') }, onError: e => notificar(mensajeError(e), 'error') })
  const descargar = async externo => {
    const pestana = window.open('about:blank', '_blank')
    if (pestana) pestana.opener = null
    try { const blob = await descargarInformeExterno(externo.id); const url = URL.createObjectURL(blob); if (pestana) pestana.location = url; else window.open(url, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(url), 60000) } catch (e) { pestana?.close(); notificar(mensajeError(e), 'error') }
  }
  return <details className="lab-area-study rxe-desplegable" open={abierto} onToggle={e => setAbierto(e.currentTarget.open)}>
    <summary><h2>3. Informes externos</h2><span>{informes.length ? `${informes.length} adjunto${informes.length === 1 ? '' : 's'}` : 'Opcional'}</span></summary>
    {editable && <form className="rxe-form-grid" onSubmit={e => { e.preventDefault(); adjuntar.mutate() }}>
      <label>PDF *<input type="file" accept="application/pdf,.pdf" required onChange={e => setArchivo(e.target.files[0] || null)} /></label>
      <label>Establecimiento *<input required value={campos.establecimiento} onChange={e => setCampos({ ...campos, establecimiento: e.target.value })} /></label>
      <label>Profesional<input value={campos.profesional} onChange={e => setCampos({ ...campos, profesional: e.target.value })} /></label>
      <label>Fecha del informe<input type="date" value={campos.fecha_informe} onChange={e => setCampos({ ...campos, fecha_informe: e.target.value })} /></label>
      <label className="rxe-span">Observaciones<textarea value={campos.observaciones} onChange={e => setCampos({ ...campos, observaciones: e.target.value })} /></label>
      <Boton type="submit" disabled={adjuntar.isPending || !archivo || !campos.establecimiento.trim()}>Adjuntar informe externo</Boton>
    </form>}
    <ul className="rxe-lista">{informes.map(externo => <li key={externo.id}><div><strong>Informe externo — {externo.establecimiento}</strong><span>{externo.profesional || 'Profesional no informado'} · {externo.fecha_informe || externo.fecha_carga}</span></div>
      <Boton variante="secundario" onClick={() => descargar(externo)}>Descargar</Boton>{editable && <Boton variante="secundario" onClick={() => setRetirar(externo)}>Retirar</Boton>}</li>)}</ul>
    {retirar && <ConfirmarAccion titulo="Retirar informe externo" textoConfirmar="Retirar" peligro pendiente={quitar.isPending} onCancelar={() => setRetirar(null)} onConfirmar={() => motivo.trim() && quitar.mutate()}>
      <label className="lab-search-label">Motivo *<textarea value={motivo} onChange={e => setMotivo(e.target.value)} /></label>
    </ConfirmarAccion>}
  </details>
}

const POSICIONES = { bipedestacion: 'Bipedestación', sedestacion: 'Sedestación', decubito_supino: 'Decúbito supino', decubito_prono: 'Decúbito prono', decubito_lateral: 'Decúbito lateral' }

export default function SeccionAdquisicion({ estudioId, detalle }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion()
  const [form, setForm] = useState(VACIO); const [pendientes, setPendientes] = useState([])
  const clave = ['radiologia', 'estudio', estudioId]
  const actualizar = dato => queryClient.setQueryData(clave, dato)
  useEffect(() => { const a = detalle.adquisicion; setForm(a ? { ...VACIO, ...a, fecha_hora_adquisicion: aLocal(a.fecha_hora_adquisicion), parametros: a.parametros || {} } : VACIO) }, [detalle.adquisicion])
  const fallo = e => notificar(mensajeError(e), 'error')
  const datosRegistro = () => ({
    proyecciones_realizadas: form.proyecciones_realizadas,
    lateralidad_realizada: form.lateralidad_realizada || null,
    posicion_paciente: form.posicion_paciente || null,
    fecha_hora_adquisicion: form.fecha_hora_adquisicion ? new Date(form.fecha_hora_adquisicion).toISOString() : null,
    operador_nombre: form.operador_nombre?.trim() || null,
    calidad: form.calidad || null,
    limitaciones: form.limitaciones?.trim() || null,
    repeticiones: Number(form.repeticiones || 0),
    motivo_repeticion: form.motivo_repeticion?.trim() || null,
    parametros: parametrosANumeros(form.parametros),
    observaciones: form.observaciones?.trim() || null,
  })
  const guardar = useMutation({ mutationFn: () => guardarAdquisicion(estudioId, datosRegistro()), onSuccess: d => { actualizar(d); notificar('Registro de adquisición guardado.', 'exito') }, onError: fallo })
  const completar = useMutation({ mutationFn: async () => { if (editableRegistro) await guardarAdquisicion(estudioId, datosRegistro()); return completarAdquisicion(estudioId) }, onSuccess: d => { actualizar(d); setPendientes([]); notificar('Adquisición completada.', 'exito') }, onError: e => { setPendientes(pendientesDeError(e)); fallo(e) } })
  const subir = useMutation({ mutationFn: ({ archivos, proyecciones }) => subirImagenes(estudioId, archivos, proyecciones), onSuccess: (d, variables) => { actualizar(d); variables.fin(); notificar('Imágenes subidas.', 'exito') }, onError: fallo })
  const asignar = useMutation({ mutationFn: ({ id, codigo }) => asignarProyeccion(estudioId, id, codigo), onSuccess: actualizar, onError: fallo })
  const retirar = useMutation({ mutationFn: ({ id, motivo }) => retirarImagen(estudioId, id, motivo), onSuccess: (d, variables) => { actualizar(d); variables.fin(); notificar('Imagen retirada.', 'exito') }, onError: fallo })
  const editableRegistro = Boolean(detalle.permisos.registrar_adquisicion); const editableImagenes = Boolean(detalle.permisos.gestionar_imagenes)
  const ocupado = guardar.isPending || completar.isPending || subir.isPending || asignar.isPending || retirar.isPending
  const proyecciones = detalle.config?.proyecciones || []
  const alternar = codigo => setForm(f => ({ ...f, proyecciones_realizadas: f.proyecciones_realizadas.includes(codigo) ? f.proyecciones_realizadas.filter(x => x !== codigo) : [...f.proyecciones_realizadas, codigo] }))
  const hayImagenes = (detalle.imagenes || []).length > 0
  const registroActivo = editableRegistro && hayImagenes && !ocupado
  const resumen = resumenAdquisicion(form, detalle.config || {}, (detalle.imagenes || []).length)
  const motivo = pendientes.length ? pendientes.join(' ') : resumen.faltan.length ? `Para completar falta: ${resumen.faltan.join(' ')}` : null
  const [confirmar, setConfirmar] = useState(false)
  return <div className="rxe-workspace">
    <PanelImagenes imagenes={detalle.imagenes || []} vacio={editableImagenes && <>
      <h2>1. Sube las imágenes del estudio</h2>
      <p>Primero las imágenes: quedarán a la vista aquí mientras completas el registro técnico.</p>
      <ZonaCarga proyecciones={proyecciones} disabled={ocupado} onSubir={(archivos, proys, fin) => subir.mutate({ archivos, proyecciones: proys, fin })} />
    </>} />
    <div className="rxe-work-form">
      {editableRegistro && <ResumenAvance resumen={resumen} motivoBloqueo={motivo} />}
      <section className="lab-area-study"><header><h2>1. Imágenes *</h2><small>{(detalle.imagenes || []).length} en el estudio</small></header>
        {!hayImagenes && editableImagenes && <p className="lab-form-hint">Empieza subiendo las imágenes en el panel de la izquierda: así las ves mientras completas el registro.</p>}
        {hayImagenes && editableImagenes && <ZonaCarga proyecciones={proyecciones} disabled={ocupado} onSubir={(archivos, proys, fin) => subir.mutate({ archivos, proyecciones: proys, fin })} />}
        <GaleriaImagenes imagenes={detalle.imagenes || []} proyecciones={proyecciones} editable={editableImagenes} ocupado={ocupado} onAsignar={(id, codigo) => asignar.mutate({ id, codigo })} onRetirar={(id, motivo, fin) => motivo.trim() && retirar.mutate({ id, motivo: motivo.trim(), fin })} />
      </section>
      <section className="lab-area-study"><header><h2>2. Registro técnico</h2>{!editableRegistro ? <small>Solo lectura</small> : !hayImagenes && <small>Se habilita al subir la primera imagen</small>}</header>
        <form id="rx-registro" className="rxe-form-grid" onSubmit={e => { e.preventDefault(); guardar.mutate() }}>
          <fieldset className="rxe-span"><legend>Proyecciones realizadas *</legend>{proyecciones.map(p => <label className="rxe-check" key={p.codigo}><input type="checkbox" checked={form.proyecciones_realizadas.includes(p.codigo)} disabled={!registroActivo} onChange={() => alternar(p.codigo)} />{p.nombre}</label>)}
            {editableRegistro && <Boton variante="secundario" disabled={!registroActivo} onClick={() => setForm({ ...form, proyecciones_realizadas: [...(detalle.estudio.detalle?.proyecciones_solicitadas || [])] })}>Usar las solicitadas</Boton>}</fieldset>
          {detalle.config?.requiere_lateralidad && <label>Lateralidad realizada *<select value={form.lateralidad_realizada || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, lateralidad_realizada: e.target.value })}><option value="">Seleccionar</option><option value="derecha">Derecha</option><option value="izquierda">Izquierda</option>{detalle.config.permite_bilateral && <option value="bilateral">Bilateral</option>}</select></label>}
          <label>Posición del paciente<select value={form.posicion_paciente || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, posicion_paciente: e.target.value })}><option value="">Seleccionar</option>{Object.entries(POSICIONES).map(([x, nombre]) => <option key={x} value={x}>{nombre}</option>)}</select></label>
          <label>Fecha y hora *<input type="datetime-local" value={form.fecha_hora_adquisicion || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, fecha_hora_adquisicion: e.target.value })} /></label>
          <label>Operador<input value={form.operador_nombre || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, operador_nombre: e.target.value })} /></label>
          <label>Calidad<select value={form.calidad || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, calidad: e.target.value })}><option value="">Seleccionar</option><option value="adecuada">Adecuada</option><option value="limitada">Limitada</option><option value="no_diagnostica">No diagnóstica</option></select></label>
          <label className="rxe-span">Observaciones<textarea value={form.observaciones || ''} disabled={!registroActivo} onChange={e => setForm({ ...form, observaciones: e.target.value })} /></label>
        </form>
      </section>
      <InformesExternos estudioId={estudioId} informes={detalle.informes_externos || []} editable={Boolean(detalle.permisos.adjuntar_externo)} actualizar={actualizar} />
      {editableRegistro && <footer className="lab-area-result-actions rxe-pie">
        <span className="lab-form-hint">Guarda el registro antes de salir. Al completar, el estudio pasa al informe.</span>
        <Boton variante="secundario" type="submit" form="rx-registro" disabled={!registroActivo}>{guardar.isPending ? 'Guardando…' : 'Guardar registro'}</Boton>
        <Boton disabled={ocupado || resumen.faltan.length > 0} title={motivo ?? undefined} onClick={() => setConfirmar(true)}>Completar adquisición</Boton>
      </footer>}
    </div>
    {confirmar && <ConfirmarAccion titulo="Completar adquisición" textoConfirmar="Completar adquisición" textoCancelar="Seguir revisando" pendiente={completar.isPending}
      onCancelar={() => setConfirmar(false)} onConfirmar={() => completar.mutate(undefined, { onSettled: () => setConfirmar(false) })}>
      <p>Se guardará el registro técnico y el estudio pasará a <strong>pendiente de informe</strong> con {(detalle.imagenes || []).length} {(detalle.imagenes || []).length === 1 ? 'imagen' : 'imágenes'}.</p>
    </ConfirmarAccion>}
  </div>
}
