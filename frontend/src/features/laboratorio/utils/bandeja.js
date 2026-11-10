import { AREAS_LABORATORIO, ESTADOS_FINALES } from './catalogos.js'

const AREAS_CON_PANTALLA = new Set(AREAS_LABORATORIO.map(({ codigo }) => codigo))
const MINUTO = 60 * 1000
const HORA = 60 * MINUTO
const DIA = 24 * HORA

export function progresoSolicitud(estudios) {
  const finalizados = estudios.filter((estudio) => ESTADOS_FINALES.has(estudio.estado)).length
  return { total: estudios.length, finalizados, completa: estudios.length > 0 && finalizados === estudios.length }
}

/** Lo siguiente que el personal debe hacer con la solicitud, con su destino. */
export function siguienteAccion(solicitud) {
  const { id, estudios } = solicitud
  if (estudios.some((estudio) => estudio.estado === 'pendiente_muestra')) {
    return { tipo: 'muestra', etiqueta: 'Registrar muestra', ruta: `/laboratorio/solicitudes/${id}?accion=muestra` }
  }
  const enPreparacion = estudios.find((estudio) => estudio.estado === 'resultado_en_preparacion')
  if (enPreparacion) {
    const ruta = AREAS_CON_PANTALLA.has(enPreparacion.categoria_laboratorio)
      ? `/laboratorio/solicitudes/${id}/areas/${enPreparacion.categoria_laboratorio}/resultados`
      : `/laboratorio/solicitudes/${id}`
    return { tipo: 'resultados', etiqueta: 'Capturar resultados', ruta }
  }
  if (progresoSolicitud(estudios).completa) {
    return { tipo: 'informe', etiqueta: 'Ver informe', ruta: `/laboratorio/solicitudes/${id}/informe` }
  }
  return { tipo: 'abrir', etiqueta: 'Abrir solicitud', ruta: `/laboratorio/solicitudes/${id}` }
}

export function tiempoTranscurrido(fecha, ahora = Date.now()) {
  const diferencia = Math.max(0, ahora - new Date(fecha).getTime())
  if (!Number.isFinite(diferencia)) return ''
  if (diferencia < MINUTO) return 'hace un momento'
  if (diferencia < HORA) return `hace ${Math.floor(diferencia / MINUTO)} min`
  if (diferencia < DIA) return `hace ${Math.floor(diferencia / HORA)} h`
  const dias = Math.floor(diferencia / DIA)
  return `hace ${dias} ${dias === 1 ? 'día' : 'días'}`
}

/** Umbral orientativo para llamar la atención: 2 h si es urgente, 24 h si no. */
export function esperaProlongada(solicitud, ahora = Date.now()) {
  if (progresoSolicitud(solicitud.estudios).completa) return false
  const limite = solicitud.prioridad === 'urgente' ? 2 * HORA : DIA
  return ahora - new Date(solicitud.fecha_solicitud).getTime() > limite
}

export const INDICADORES_BANDEJA = [
  { codigo: 'todas', nombre: 'Solicitudes pendientes', cumple: () => true },
  { codigo: 'muestra', nombre: 'Con muestras por recibir', cumple: (s) => s.estudios.some((e) => e.estado === 'pendiente_muestra') },
  { codigo: 'preparacion', nombre: 'Con resultados en preparación', cumple: (s) => s.estudios.some((e) => e.estado === 'resultado_en_preparacion') },
  { codigo: 'urgentes', nombre: 'Solicitudes urgentes', cumple: (s) => s.prioridad === 'urgente' },
]

export const PERIODOS_FINALIZADAS = [
  { codigo: 'hoy', nombre: 'Hoy' },
  { codigo: 'semana', nombre: 'Últimos 7 días' },
  { codigo: 'mes', nombre: 'Últimos 30 días' },
  { codigo: 'todas', nombre: 'Todas' },
]

function inicioPeriodo(periodo, ahora) {
  if (periodo === 'hoy') {
    const hoy = new Date(ahora)
    hoy.setHours(0, 0, 0, 0)
    return hoy.getTime()
  }
  if (periodo === 'semana') return ahora - 7 * DIA
  if (periodo === 'mes') return ahora - 30 * DIA
  return null
}

export function filtrarSolicitudes(solicitudes, { busqueda = '', indicador = 'todas', periodo = 'todas', ahora = Date.now() } = {}) {
  const termino = busqueda.trim().toLocaleLowerCase()
  const criterio = INDICADORES_BANDEJA.find(({ codigo }) => codigo === indicador)?.cumple ?? (() => true)
  const desde = inicioPeriodo(periodo, ahora)
  return solicitudes.filter((solicitud) => criterio(solicitud)
    && (desde === null || new Date(solicitud.fecha_solicitud).getTime() >= desde)
    && (!termino || [solicitud.paciente_nombre, solicitud.referencia,
      ...solicitud.estudios.flatMap((estudio) => [estudio.referencia_estudio, estudio.tipo_estudio_nombre])]
      .some((valor) => valor?.toLocaleLowerCase().includes(termino))))
}
