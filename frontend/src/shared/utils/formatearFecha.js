export function formatearFecha(fechaISO) {
  return new Date(fechaISO).toLocaleDateString('es-BO')
}
