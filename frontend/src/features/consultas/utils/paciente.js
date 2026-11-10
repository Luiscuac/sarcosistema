import { describirEdad } from '../../../shared/utils/edad.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'

/**
 * Fecha visible (dd/mm/aaaa) en hora local.
 * Una fecha de calendario ("2026-11-10") se toma como día local; un instante con hora
 * ("2026-11-11T01:30:00+00:00") se convierte a la zona del navegador. Cortar el texto
 * mostraba el día siguiente en las atenciones de la noche (UTC-4).
 */
export function fecha(valor) {
  if (!valor) return 'No registrada'
  const texto = String(valor)
  return formatearFecha(/^\d{4}-\d{2}-\d{2}$/.test(texto) ? texto : fechaLocalDe(new Date(texto)))
}

/** Fecha de calendario local "AAAA-MM-DD" de un instante (sin pasar por UTC). */
export function fechaLocalDe(instante = new Date()) {
  const dos = (numero) => String(numero).padStart(2, '0')
  return `${instante.getFullYear()}-${dos(instante.getMonth() + 1)}-${dos(instante.getDate())}`
}

export function edad(nacimiento) {
  return describirEdad(nacimiento) || 'No registrada'
}

/** El registro se publicó hoy (en hora local). */
export function esDeHoy(instante, hoy = new Date()) {
  return Boolean(instante) && fechaLocalDe(new Date(instante)) === fechaLocalDe(hoy)
}
