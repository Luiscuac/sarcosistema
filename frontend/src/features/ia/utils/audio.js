export function mensajeDeError(error) {
  if (error?.name === 'NotAllowedError' || error?.name === 'PermissionDeniedError') {
    return 'No se concedió acceso al micrófono. Permite el acceso en el navegador e inténtalo de nuevo.'
  }
  if (error?.name === 'NotFoundError' || error?.name === 'DevicesNotFoundError') {
    return 'No se encontró un micrófono disponible en este dispositivo.'
  }
  const estado = error.response?.status
  if (estado === 413) return 'La grabación supera el límite de 20 MB.'
  if (estado === 415) return 'El navegador generó un formato de audio que el servidor no admite.'
  if (estado === 503) return 'El modelo local no está disponible o no pudo procesar el audio.'
  if (!error.response && error.name === 'NotSupportedError') return 'Este navegador no permite grabar audio en un formato compatible.'
  if (!error.response) return 'No se pudo conectar con el servidor. Comprueba que el backend esté iniciado.'
  return 'No se pudo transcribir la grabación. Inténtalo de nuevo.'
}

export function formatearTiempo(segundos) {
  const minutos = Math.floor(segundos / 60).toString().padStart(2, '0')
  const resto = (segundos % 60).toString().padStart(2, '0')
  return `${minutos}:${resto}`
}
