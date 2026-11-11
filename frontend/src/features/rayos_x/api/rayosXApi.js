import api from '../../../shared/api/httpClient.js'

const modalidad = 'rayos_x'

export const listarBandeja = async () => (await api.get('/imagenes/bandeja', { params: { modalidad } })).data
export const obtenerEstudio = async id => (await api.get(`/imagenes/estudios/${id}`, { params: { modalidad } })).data
export const obtenerArchivoImagen = async archivoId =>
  (await api.get(`/imagenes/archivos/${archivoId}`, { responseType: 'blob' })).data

export const subirInforme = async (estudioId, descripcion, archivos) => {
  const datos = new FormData()
  datos.append('descripcion', descripcion)
  for (const archivo of archivos) datos.append('archivos', archivo, archivo.name)
  return (await api.post(`/imagenes/estudios/${estudioId}/informes`, datos, { params: { modalidad } })).data
}

export const publicarInforme = async estudioId =>
  (await api.post(`/imagenes/estudios/${estudioId}/informes/publicar`, null, { params: { modalidad } })).data

export const MODALIDAD_RAYOS_X = modalidad
