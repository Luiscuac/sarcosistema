const FORMATO = { day: '2-digit', month: '2-digit', year: 'numeric' }
const HORA = { hour: '2-digit', minute: '2-digit', hour12: false }
const SOLO_FECHA = /^\d{4}-\d{2}-\d{2}$/

/**
 * Fecha en formato dd/mm/aaaa.
 * Una fecha de calendario ("1990-01-05") se toma como día local: si se parseara como instante UTC,
 * en zonas horarias negativas (Bolivia, UTC-4) se mostraría el día anterior.
 * Un instante con hora ("2026-11-24T01:00:00Z") se convierte a la hora local antes de tomar el día.
 */
export function formatearFecha(fechaISO) {
  const valor = String(fechaISO ?? '')
  if (SOLO_FECHA.test(valor)) {
    const [anio, mes, dia] = valor.split('-')
    return new Date(Number(anio), Number(mes) - 1, Number(dia)).toLocaleDateString('es-BO', FORMATO)
  }
  return new Date(valor).toLocaleDateString('es-BO', FORMATO)
}

/** Fecha y hora local "dd/mm/aaaa hh:mm" (24 h). Sin valor o inválido devuelve `vacio`. */
export function formatearFechaHora(instante, vacio = '—') {
  if (!instante) return vacio
  const fecha = new Date(instante)
  if (Number.isNaN(fecha.getTime())) return vacio
  return `${fecha.toLocaleDateString('es-BO', FORMATO)} ${fecha.toLocaleTimeString('es-BO', HORA)}`
}

/** Hoy como "aaaa-mm-dd" en hora local (para <input type="date"> y valores por defecto). */
export function fechaHoy(ahora = new Date()) {
  const dos = n => String(n).padStart(2, '0')
  return `${ahora.getFullYear()}-${dos(ahora.getMonth() + 1)}-${dos(ahora.getDate())}`
}
