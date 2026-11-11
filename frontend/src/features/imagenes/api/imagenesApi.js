import api from '../../../shared/api/httpClient.js'

export const listarBandeja = async () => (await api.get('/imagenes/bandeja')).data

export const obtenerEstudio = async (id) => (await api.get(`/imagenes/estudios/${id}`)).data

export const obtenerArchivoImagen = async (archivoId) =>
  (await api.get(`/imagenes/archivos/${archivoId}`, { responseType: 'blob' })).data

export const subirInforme = async (estudioId, descripcion, archivos) => {
  const datos = new FormData()
  datos.append('descripcion', descripcion)
  for (const archivo of archivos) datos.append('archivos', archivo, archivo.name)
  return (await api.post(`/imagenes/estudios/${estudioId}/informes`, datos)).data
}

export const publicarInforme = async (estudioId) =>
  (await api.post(`/imagenes/estudios/${estudioId}/informes/publicar`)).data

export const descargarArchivo = async (archivoId, nombreOriginal) => {
  const respuesta = await api.get(`/imagenes/archivos/${archivoId}`, { responseType: 'blob' })
  const url = URL.createObjectURL(respuesta.data)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombreOriginal || `archivo-${archivoId}`
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}
