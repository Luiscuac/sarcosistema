import httpClient from '../../../../shared/api/httpClient.js'

export async function transcribirAudio(archivo, nombre = 'grabacion.webm', signal) {
  const datos = new FormData()
  datos.append('archivo', archivo, nombre)
  const { data } = await httpClient.post('/ia/transcribir', datos, { signal })
  return data
}
