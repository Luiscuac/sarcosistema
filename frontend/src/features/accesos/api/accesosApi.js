import httpClient from '../../../shared/api/httpClient.js'

export async function iniciarSesion(credenciales) {
  const { data } = await httpClient.post('/accesos/login', credenciales)
  return data
}

export async function obtenerUsuarioActual() {
  const { data } = await httpClient.get('/accesos/yo')
  return data
}
