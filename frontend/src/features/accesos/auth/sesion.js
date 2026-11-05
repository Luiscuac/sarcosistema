export function actualizarSesion(queryClient, storage, token) {
  // clear() también destruye/cancela las consultas pendientes: no mezclar sesiones.
  queryClient.clear()
  if (token) storage.setItem('token', token)
  else storage.removeItem('token')
}
