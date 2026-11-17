import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import ConfirmarAccion from '../../../laboratorio/components/ConfirmarAccion.jsx'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import {
  adjuntarInformeExterno, asignarProyeccion, completarAdquisicion, descargarInformeExterno,
  guardarAdquisicion, mensajeErrorApi, pendientesDeError, retirarImagen, retirarInformeExterno, subirImagenes,
} from '../../api/radiologiaApi.js'
import GaleriaImagenes from './GaleriaImagenes.jsx'
import { parametrosANumeros, tamanoLegible, validarArchivoImagen } from '../utils/informe.js'

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
    {items.length > 0 && <button type="button" className="primary-button" disabled={disabled || !validos}
      onClick={() => onSubir(items.map(x => x.archivo), items.map(x => x.proyeccion), () => setItems([]))}>Subir imágenes</button>}
  </div>
}

function InformesExternos({ estudioId, informes, editable, actualizar }) {
  const { notificar } = useNotificacion()
  const [archivo, setArchivo] = useState(null)
  const [campos, setCampos] = useState({ establecimiento: '', profesional: '', fecha_informe: '', observaciones: '' })
  const [retirar, setRetirar] = useState(null); const [motivo, setMotivo] = useState('')
  const adjuntar = useMutation({ mutationFn: () => adjuntarInformeExterno(estudioId, archivo, campos), onSuccess: dato => { actualizar(dato); setArchivo(null); setCampos({ establecimiento: '', profesional: '', fecha_informe: '', observaciones: '' }); notificar('Informe externo adjuntado.', 'exito') }, onError: e => notificar(mensajeErrorApi(e), 'error') })
  const quitar = useMutation({ mutationFn: () => retirarInformeExterno(estudioId, retirar.id, motivo.trim()), onSuccess: dato => { actualizar(dato); setRetirar(null); setMotivo(''); notificar('Informe externo retirado.', 'exito') }, onError: e => notificar(mensajeErrorApi(e), 'error') })
  const descargar = async externo => {
    const pestana = window.open('about:blank', '_blank')
    if (pestana) pestana.opener = null
    try { const blob = await descargarInformeExterno(externo.id); const url = URL.createObjectURL(blob); if (pestana) pestana.location = url; else window.open(url, '_blank', 'noopener,noreferrer'); setTimeout(() => URL.revokeObjectURL(url), 60000) } catch (e) { pestana?.close(); notificar(mensajeErrorApi(e), 'error') }
  }
  return <section className="rxe-bloque"><h2>Informes externos</h2>
    {editable && <form className="rxe-form-grid" onSubmit={e => { e.preventDefault(); adjuntar.mutate() }}>
      <label>PDF *<input type="file" accept="application/pdf,.pdf" required onChange={e => setArchivo(e.target.files[0] || null)} /></label>
      <label>Establecimiento *<input required value={campos.establecimiento} onChange={e => setCampos({ ...campos, establecimiento: e.target.value })} /></label>
      <label>Profesional<input value={campos.profesional} onChange={e => setCampos({ ...campos, profesional: e.target.value })} /></label>
      <label>Fecha del informe<input type="date" value={campos.fecha_informe} onChange={e => setCampos({ ...campos, fecha_informe: e.target.value })} /></label>
      <label className="rxe-span">Observaciones<textarea value={campos.observaciones} onChange={e => setCampos({ ...campos, observaciones: e.target.value })} /></label>
      <button type="submit" className="primary-button" disabled={adjuntar.isPending || !archivo || !campos.establecimiento.trim()}>Adjuntar informe externo</button>
    </form>}
    <ul className="rxe-lista">{informes.map(externo => <li key={externo.id}><div><strong>Informe externo — {externo.establecimiento}</strong><span>{externo.profesional || 'Profesional no informado'} · {externo.fecha_informe || externo.fecha_carga}</span></div>
      <button type="button" className="lab-secondary-button" onClick={() => descargar(externo)}>Descargar</button>{editable && <button type="button" className="lab-secondary-button" onClick={() => setRetirar(externo)}>Retirar</button>}</li>)}</ul>
    {retirar && <ConfirmarAccion titulo="Retirar informe externo" textoConfirmar="Retirar" peligro pendiente={quitar.isPending} onCancelar={() => setRetirar(null)} onConfirmar={() => motivo.trim() && quitar.mutate()}>
      <label className="lab-search-label">Motivo *<textarea value={motivo} onChange={e => setMotivo(e.target.value)} /></label>
    </ConfirmarAccion>}
  </section>
}

const POSICIONES = { bipedestacion: 'Bipedestación', sedestacion: 'Sedestación', decubito_supino: 'Decúbito supino', decubito_prono: 'Decúbito prono', decubito_lateral: 'Decúbito lateral' }

export default function SeccionAdquisicion({ estudioId, detalle }) {
  const queryClient = useQueryClient(); const { notificar } = useNotificacion()
  const [form, setForm] = useState(VACIO); const [pendientes, setPendientes] = useState([])
  const clave = ['radiologia', 'estudio', estudioId]
  const actualizar = dato => queryClient.setQueryData(clave, dato)
  useEffect(() => { const a = detalle.adquisicion; setForm(a ? { ...VACIO, ...a, fecha_hora_adquisicion: aLocal(a.fecha_hora_adquisicion), parametros: a.parametros || {} } : VACIO) }, [detalle.adquisicion])
  const fallo = e => notificar(mensajeErrorApi(e), 'error')
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
  return <div className="rxe-seccion">
    <section className="rxe-bloque"><h2>Registro técnico</h2>{!editableRegistro && <p className="rxe-estado">Registro en modo de solo lectura.</p>}
      <form className="rxe-form-grid" onSubmit={e => { e.preventDefault(); guardar.mutate() }}>
        <fieldset className="rxe-span"><legend>Proyecciones realizadas</legend>{proyecciones.map(p => <label className="rxe-check" key={p.codigo}><input type="checkbox" checked={form.proyecciones_realizadas.includes(p.codigo)} disabled={!editableRegistro || ocupado} onChange={() => alternar(p.codigo)} />{p.nombre}</label>)}
          {editableRegistro && <button type="button" className="lab-secondary-button" onClick={() => setForm({ ...form, proyecciones_realizadas: [...(detalle.estudio.detalle?.proyecciones_solicitadas || [])] })}>Usar las solicitadas</button>}</fieldset>
        {detalle.config?.requiere_lateralidad && <label>Lateralidad realizada<select value={form.lateralidad_realizada || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, lateralidad_realizada: e.target.value })}><option value="">Seleccionar</option><option value="derecha">Derecha</option><option value="izquierda">Izquierda</option>{detalle.config.permite_bilateral && <option value="bilateral">Bilateral</option>}</select></label>}
        <label>Posición del paciente<select value={form.posicion_paciente || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, posicion_paciente: e.target.value })}><option value="">Seleccionar</option>{Object.entries(POSICIONES).map(([x, nombre]) => <option key={x} value={x}>{nombre}</option>)}</select></label>
        <label>Fecha y hora<input type="datetime-local" value={form.fecha_hora_adquisicion || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, fecha_hora_adquisicion: e.target.value })} /></label>
        <label>Operador<input value={form.operador_nombre || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, operador_nombre: e.target.value })} /></label>
        <label>Calidad<select value={form.calidad || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, calidad: e.target.value })}><option value="">Seleccionar</option><option value="adecuada">Adecuada</option><option value="limitada">Limitada</option><option value="no_diagnostica">No diagnóstica</option></select></label>
        <label>Repeticiones<input type="number" min="0" value={form.repeticiones} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, repeticiones: e.target.value })} /></label>
        <label className="rxe-span">Limitaciones<textarea value={form.limitaciones || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, limitaciones: e.target.value })} /></label>
        <label className="rxe-span">Motivo de repetición<textarea value={form.motivo_repeticion || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, motivo_repeticion: e.target.value })} /></label>
        <label className="rxe-span">Observaciones<textarea value={form.observaciones || ''} disabled={!editableRegistro || ocupado} onChange={e => setForm({ ...form, observaciones: e.target.value })} /></label>
        {editableRegistro && <div className="rxe-acciones rxe-span"><button type="submit" className="lab-secondary-button" disabled={ocupado}>Guardar registro</button></div>}
      </form>
    </section>
    <section className="rxe-bloque"><h2>Imágenes</h2>{editableImagenes && <ZonaCarga proyecciones={proyecciones} disabled={ocupado} onSubir={(archivos, proys, fin) => subir.mutate({ archivos, proyecciones: proys, fin })} />}
      <GaleriaImagenes imagenes={detalle.imagenes || []} proyecciones={proyecciones} editable={editableImagenes} ocupado={ocupado} onAsignar={(id, codigo) => asignar.mutate({ id, codigo })} onRetirar={(id, motivo, fin) => motivo.trim() && retirar.mutate({ id, motivo: motivo.trim(), fin })} />
    </section>
    {editableRegistro && <section className="rxe-bloque rxe-cierre"><div><h2>Completar adquisición</h2><p>Cuando el registro técnico esté guardado y las imágenes subidas, completa la adquisición para pasar al informe.</p></div>
      <button type="button" className="primary-button" disabled={ocupado} onClick={() => { setPendientes(detalle.pendientes?.adquisicion || []); if (!(detalle.pendientes?.adquisicion || []).length) completar.mutate() }}>Completar adquisición</button>
      {pendientes.length > 0 && <div className="rxe-pendientes" role="alert"><strong>Pendientes antes de completar:</strong><ul>{pendientes.map(p => <li key={p}>{p}</li>)}</ul><button type="button" className="primary-button" disabled={ocupado} onClick={() => completar.mutate()}>Comprobar y completar</button></div>}
    </section>}
    <InformesExternos estudioId={estudioId} informes={detalle.informes_externos || []} editable={Boolean(detalle.permisos.adjuntar_externo)} actualizar={actualizar} />
  </div>
}
