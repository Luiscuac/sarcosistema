/**
 * Flujo del estudio de Rayos X: qué falta en cada paso y cuál es la acción principal.
 * Las reglas de "qué falta" replican las del servidor (domain/radiologia.py) para avisar en vivo;
 * el servidor sigue siendo quien decide al completar o validar.
 */

const resumen = faltan => (total) => ({ total, completos: total - faltan.length, fueraDeRango: [], faltan })

/** Para completar la adquisición (pendientes_para_completar_adquisicion). */
export function resumenAdquisicion(form, config = {}, imagenes = 0) {
  const faltan = []
  if (!form?.proyecciones_realizadas?.length) faltan.push('Registra al menos una proyección realizada.')
  if (config.requiere_lateralidad && !form?.lateralidad_realizada) faltan.push('Indica la lateralidad realizada.')
  if (!form?.fecha_hora_adquisicion) faltan.push('Indica la fecha y hora de adquisición.')
  if (imagenes < 1) faltan.push('Adjunta al menos una imagen.')
  return resumen(faltan)(config.requiere_lateralidad ? 4 : 3)
}

const vacio = valor => valor == null || (typeof valor === 'string' && !valor.trim())

/** Para validar el informe (pendientes_para_validar). */
export function resumenInforme(contenido = {}, textoFinal = null, imagenes = 0, externo = false) {
  const faltan = []
  if (vacio(contenido.generales?.conclusion)) faltan.push('Redacta la conclusión o impresión diagnóstica.')
  const hayHallazgo = Object.values(contenido.apartados || {}).some(v => !vacio(v))
  if (!hayHallazgo && vacio(textoFinal)) faltan.push('Registra al menos un hallazgo.')
  if (imagenes < 1 && !externo) faltan.push('El estudio no tiene imágenes asociadas.')
  return resumen(faltan)(3)
}

const ETAPA_A_PASO = { pendiente_realizacion: 1, en_adquisicion: 1, pendiente_informe: 2, borrador: 2, validado: 3, entregado: 4 }

/** Índice del paso actual en Solicitud → Adquisición → Informe → Entrega (4 = todo hecho). */
export const pasoActualRx = etapa => ETAPA_A_PASO[etapa] ?? 0

/** Acción principal del detalle según la etapa y los permisos (como en Laboratorio). */
export function accionPrincipalRx(detalle) {
  const base = `/rayos-x/gestion/estudios/${detalle.estudio.estudio_id}`
  const { etapa } = detalle.estudio
  const p = detalle.permisos || {}
  if (etapa === 'pendiente_realizacion' && p.registrar_adquisicion) return { etiqueta: 'Registrar adquisición', ruta: `${base}/adquisicion` }
  if (etapa === 'en_adquisicion' && p.registrar_adquisicion) return { etiqueta: 'Continuar la adquisición', ruta: `${base}/adquisicion` }
  if (etapa === 'pendiente_informe' && p.redactar_informe) return { etiqueta: 'Redactar informe', ruta: `${base}/informe` }
  if (etapa === 'borrador' && p.redactar_informe) return { etiqueta: 'Continuar el informe', ruta: `${base}/informe` }
  if (p.entregar) return { etiqueta: 'Registrar entrega', accion: 'entregar' }
  if (['validado', 'entregado'].includes(etapa)) return { etiqueta: 'Ver informe impreso', ruta: `${base}/impresion` }
  return null
}
