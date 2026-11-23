import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useBlocker, useNavigate } from 'react-router-dom'
import ResumenAvance from '../../../../shared/ui/ResumenAvance.jsx'
import { useNotificacion } from '../../../../shared/notifications/NotificationContext.jsx'
import * as api from '../../api/ecografiaApi.js'
import { agregarArchivos, contarImagenes, iniciarDatos, motivoBloqueoEco, resumenRegistro } from '../../informe.js'
import ConfirmarPublicacionEco from './ConfirmarPublicacionEco.jsx'
import { SeccionAdjuntos, SeccionCierre, SeccionDatos, SeccionHallazgos } from './Secciones.jsx'
import Boton from '../../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'

/** Registro por órganos: mismo esquema que la captura de resultados de Laboratorio. */
export default function RegistroHallazgos({ estudio }) {
  const cache = useQueryClient()
  const navegar = useNavigate()
  const { notificar } = useNotificacion()
  const [datos, setDatos] = useState(() => iniciarDatos(estudio))
  const [nuevos, setNuevos] = useState([])
  const [guardados, setGuardados] = useState(estudio.informe?.archivos || [])
  const [informe, setInforme] = useState(estudio.informe)
  const [cambio, setCambio] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  const [confirmando, setConfirmando] = useState(false)
  const organos = estudio.organos
  const resumen = resumenRegistro(datos, organos, contarImagenes(guardados, nuevos))
  const motivoBloqueo = motivoBloqueoEco({ faltan: resumen.faltan, cambio, guardado: Boolean(informe?.datos_ecografia) })

  // Aviso del navegador al cerrar o recargar con cambios sin guardar.
  useEffect(() => {
    if (!cambio) return undefined
    const avisar = e => { e.preventDefault(); e.returnValue = '' }
    window.addEventListener('beforeunload', avisar)
    return () => window.removeEventListener('beforeunload', avisar)
  }, [cambio])

  // Salir por la navegación del sistema con cambios sin guardar pide confirmación.
  const bloqueo = useBlocker(cambio)
  useEffect(() => {
    if (bloqueo.state !== 'blocked') return
    if (window.confirm('Hay cambios sin guardar. ¿Salir del registro?')) bloqueo.proceed()
    else bloqueo.reset()
  }, [bloqueo])

  const marcar = cambiar => (...args) => { cambiar(...args); setCambio(true) }
  const cambiar = marcar((campo, valor) => setDatos(d => ({ ...d, [campo]: valor })))
  const cambiarOrgano = marcar((organo, valor) => setDatos(d => ({ ...d, evaluaciones: { ...d.evaluaciones, [organo]: valor } })))

  async function guardar(e) {
    e.preventDefault(); setOcupado(true)
    try {
      const nuevo = await api.subirInforme(estudio.estudio_id, '', nuevos, { datos, conservar: guardados.map(a => a.id) })
      setInforme(nuevo); setGuardados(nuevo.archivos); setNuevos([]); setDatos(nuevo.datos_ecografia); setCambio(false)
      cache.setQueryData(['ecografia', 'estudio', estudio.estudio_id], { ...estudio, estado: 'resultado_en_preparacion', informe: nuevo })
      await cache.invalidateQueries({ queryKey: ['ecografia', 'bandeja'] })
      notificar('Borrador guardado con sus adjuntos.', 'exito')
    } catch (err) { notificar(mensajeError(err, 'No se pudo guardar el borrador.'), 'error') }
    finally { setOcupado(false) }
  }

  async function publicar() {
    setOcupado(true)
    try {
      await api.publicarInforme(estudio.estudio_id)
      await cache.invalidateQueries({ queryKey: ['ecografia'] })
      notificar('Informe publicado. El médico ya puede consultarlo en la ficha del paciente.', 'exito')
      navegar(`/ecografia/estudios/${estudio.estudio_id}/informe`)
    } catch (err) { notificar(mensajeError(err, 'No se pudo publicar el informe.'), 'error'); setConfirmando(false) }
    finally { setOcupado(false) }
  }

  return <>
    <header className="lab-area-results-header">
      <p className="lab-eyebrow">REGISTRO DE ECOGRAFÍA · {estudio.referencia_estudio}</p>
      <h1>{estudio.tipo_estudio_nombre}</h1>
      <p>{estudio.paciente_nombre}{estudio.codigo_paciente ? ` · ${estudio.codigo_paciente}` : ''}{estudio.medico_solicitante ? ` · Solicitó ${estudio.medico_solicitante}` : ''}</p>
    </header>
    <form className="lab-area-result-form eco-registro" onSubmit={guardar}>
      <ResumenAvance resumen={resumen} motivoBloqueo={motivoBloqueo} />
      <SeccionDatos datos={datos} cambiar={cambiar} requiereZona={['ECO_DOPPLER', 'ECO_PARTES_BLANDAS'].includes(datos.tipo)} deshabilitado={ocupado} />
      <SeccionHallazgos organos={organos} evaluaciones={datos.evaluaciones} cambiarOrgano={cambiarOrgano} deshabilitado={ocupado} />
      <SeccionAdjuntos guardados={guardados} nuevos={nuevos} maximo={estudio.max_archivos} deshabilitado={ocupado}
        onAgregar={lista => {
          try { setNuevos(agregarArchivos(nuevos, lista, estudio.max_archivos, guardados.length)); setCambio(true) }
          catch (err) { notificar(err.message, 'error') }
        }}
        onQuitarGuardado={marcar(id => setGuardados(lista => lista.filter(a => a.id !== id)))}
        onQuitarNuevo={marcar(i => setNuevos(lista => lista.filter((_, n) => n !== i)))} />
      <SeccionCierre datos={datos} cambiar={cambiar} deshabilitado={ocupado} />
      <footer className="lab-area-result-actions eco-acciones-pie">
        <span className={`eco-estado-guardado${cambio ? ' es-pendiente' : ''}`} role="status">{cambio ? 'Cambios sin guardar' : informe ? 'Borrador guardado' : 'Aún sin guardar'}</span>
        <button type="submit" disabled={ocupado || (!cambio && Boolean(informe))}>{ocupado ? 'Guardando…' : 'Guardar borrador'}</button>
        <Boton disabled={ocupado || Boolean(motivoBloqueo)} title={motivoBloqueo ?? undefined}
          onClick={() => setConfirmando(true)}>Revisar y publicar</Boton>
      </footer>
    </form>
    {confirmando && <ConfirmarPublicacionEco estudio={estudio} datos={datos} guardados={guardados} pendiente={ocupado}
      onConfirmar={publicar} onCancelar={() => setConfirmando(false)} />}
  </>
}
