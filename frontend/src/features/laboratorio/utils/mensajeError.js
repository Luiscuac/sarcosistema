/** Convierte un error de Axios en un mensaje comprensible, sin exponer detalles técnicos. */
export function mensajeError(error, predeterminado = 'No se pudo completar la acción. Inténtalo de nuevo.') {
  const detalle = error?.response?.data?.detail
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    const mensajes = detalle.map((item) => item?.msg).filter(Boolean)
    return mensajes.length ? mensajes.join(' · ') : predeterminado
  }
  if (error?.code === 'ERR_NETWORK' || (error?.request && !error?.response)) {
    return 'No hay conexión con el sistema. Comprueba la red e inténtalo de nuevo.'
  }
  return predeterminado
}
