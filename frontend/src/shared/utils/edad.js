/** Edad cumplida en años a partir de una fecha de calendario "AAAA-MM-DD". */
export function calcularEdad(fechaNacimiento, hoy = new Date()) {
  const coincidencia = String(fechaNacimiento ?? '').match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!coincidencia) return null
  const [, anio, mes, dia] = coincidencia.map(Number)
  let edad = hoy.getFullYear() - anio
  const cumplioEsteAnio = hoy.getMonth() + 1 > mes || (hoy.getMonth() + 1 === mes && hoy.getDate() >= dia)
  if (!cumplioEsteAnio) edad -= 1
  return edad >= 0 ? edad : null
}

export function describirEdad(fechaNacimiento, hoy = new Date()) {
  const edad = calcularEdad(fechaNacimiento, hoy)
  if (edad === null) return ''
  return `${edad} ${edad === 1 ? 'año' : 'años'}`
}
