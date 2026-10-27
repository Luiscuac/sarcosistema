import httpClient from '../../../../shared/api/httpClient.js'

export async function listarRegistrosPrueba() {
  const { data } = await httpClient.get('/ia/transcriptor/registros')
  return data
}

