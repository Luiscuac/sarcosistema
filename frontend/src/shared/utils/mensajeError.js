/** Mensaje estándar de un error de la API (Axios) para cualquier pantalla, sin exponer detalles técnicos. */
export function mensajeError(error, predeterminado = 'No se pudo completar la acción. Inténtalo de nuevo.') {
  const detalle = error?.response?.data?.detail
  if (typeof detalle === 'string') return detalle
  if (typeof detalle?.mensaje === 'string') return detalle.mensaje
  if (Array.isArray(detalle)) {
    const mensajes = detalle.map((item) => item?.msg).filter(Boolean)
    return mensajes.length ? mensajes.join(' · ') : predeterminado
  }
  if (error?.code === 'ERR_NETWORK' || (error?.request && !error?.response)) {
    return 'No hay conexión con el sistema. Comprueba la red e inténtalo de nuevo.'
  }
  if (error?.response?.status === 403) return 'Tu rol no permite esta acción.'
  return predeterminado
}
