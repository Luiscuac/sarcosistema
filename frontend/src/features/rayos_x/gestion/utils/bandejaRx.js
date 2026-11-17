export const INDICADORES_RX = [
  { codigo: 'pendiente_realizacion', nombre: 'Pendientes de realización', cumple: (e) => e.etapa === 'pendiente_realizacion' },
  { codigo: 'en_adquisicion', nombre: 'En adquisición', cumple: (e) => e.etapa === 'en_adquisicion' },
  { codigo: 'pendiente_informe', nombre: 'Pendientes de informe', cumple: (e) => e.etapa === 'pendiente_informe' },
  { codigo: 'borrador', nombre: 'En borrador', cumple: (e) => e.etapa === 'borrador' },
  { codigo: 'urgentes', nombre: 'Urgentes', cumple: (e) => e.prioridad === 'urgente' },
]

const normalizar = (valor) => String(valor ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase()
const indiceTriaje = (estudio) => Number.isFinite(Number(estudio.triaje?.indice)) ? Number(estudio.triaje.indice) : -Infinity
const fecha = (estudio) => {
  const valor = new Date(estudio.fecha_solicitud).getTime()
  return Number.isFinite(valor) ? valor : Infinity
}

/** Urgentes primero, luego mayor indice de triaje y finalmente solicitudes mas antiguas. */
export function compararEstudios(a, b) {
  const urgencia = Number(b.prioridad === 'urgente') - Number(a.prioridad === 'urgente')
  if (urgencia) return urgencia
  const triaje = indiceTriaje(b) - indiceTriaje(a)
  if (triaje) return triaje
  return fecha(a) - fecha(b)
}

export function filtrarYOrdenarEstudios(estudios, filtros = {}) {
  const termino = normalizar(filtros.busqueda).trim()
  const indicador = INDICADORES_RX.find((item) => item.codigo === filtros.indicador)
  return [...(estudios ?? [])].filter((estudio) => {
    const coincideTexto = !termino || [
      estudio.paciente_nombre, estudio.paciente_documento, estudio.referencia_solicitud,
      estudio.referencia_estudio, estudio.tipo_estudio_nombre,
    ].some((valor) => normalizar(valor).includes(termino))
    return coincideTexto
      && (!filtros.categoria || estudio.categoria === filtros.categoria)
      && (!filtros.etapa || estudio.etapa === filtros.etapa)
      && (!indicador || indicador.cumple(estudio))
  }).sort(compararEstudios)
}

export function agruparPorSolicitud(estudios) {
  const grupos = new Map()
  for (const estudio of estudios ?? []) {
    const id = estudio.solicitud_id
    if (!grupos.has(id)) grupos.set(id, {
      id,
      referencia: estudio.referencia_solicitud,
      paciente_id: estudio.paciente_id,
      paciente_nombre: estudio.paciente_nombre,
      paciente_documento: estudio.paciente_documento,
      fecha_solicitud: estudio.fecha_solicitud,
      prioridad: estudio.prioridad,
      medico_solicitante: estudio.medico_solicitante,
      estudios: [],
    })
    grupos.get(id).estudios.push(estudio)
  }
  return [...grupos.values()]
}

export function contarIndicadores(estudios) {
  return Object.fromEntries(INDICADORES_RX.map((indicador) => [
    indicador.codigo,
    (estudios ?? []).filter(indicador.cumple).length,
  ]))
}
