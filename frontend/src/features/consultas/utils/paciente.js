export function fecha(valor) {
  return valor ? new Date(`${valor.slice(0, 10)}T12:00:00`).toLocaleDateString('es-BO') : 'No registrada'
}

export function edad(nacimiento) {
  if (!nacimiento) return 'No registrada'
  const hoy = new Date()
  const nacio = new Date(`${nacimiento.slice(0, 10)}T12:00:00`)
  const cumpleEsteAnio = hoy.getMonth() > nacio.getMonth()
    || (hoy.getMonth() === nacio.getMonth() && hoy.getDate() >= nacio.getDate())
  return `${hoy.getFullYear() - nacio.getFullYear() - (cumpleEsteAnio ? 0 : 1)} años`
}
