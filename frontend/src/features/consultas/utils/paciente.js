import { describirEdad } from '../../../shared/utils/edad.js'
import { fechaHoy, formatearFecha } from '../../../shared/utils/formatearFecha.js'

/** Fecha visible (dd/mm/aaaa) en hora local; sin valor, "No registrada". */
export function fecha(valor) {
  return valor ? formatearFecha(valor) : 'No registrada'
}

export function edad(nacimiento) {
  return describirEdad(nacimiento) || 'No registrada'
}

/** El registro se publicó hoy (en hora local). */
export function esDeHoy(instante, hoy = new Date()) {
  return Boolean(instante) && fechaHoy(new Date(instante)) === fechaHoy(hoy)
}
