import httpClient from '../../../../shared/api/httpClient.js'

export async function transcribirAudio(archivo, nombre = 'grabacion.webm') {
  const datos = new FormData()
  datos.append('archivo', archivo, nombre)
  const { data } = await httpClient.post('/ia/transcribir', datos)
  return data
}
