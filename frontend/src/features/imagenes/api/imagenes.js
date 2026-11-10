import api from '../../../shared/api/httpClient.js'

export const listarEstudios = async (pagina, signal) => (await api.get('/imagenes/estudios', { params: { pagina }, signal })).data
export const obtenerEstudio = async (id, signal) => (await api.get(`/imagenes/estudios/${id}`, { signal })).data
export const obtenerArchivo = async (estudio, archivo, signal) => (await api.get(`/imagenes/estudios/${estudio}/archivos/${archivo}`, { responseType: 'blob', signal })).data
export const solicitarAnalisis = async (id, datos) => (await api.post(`/imagenes/estudios/${id}/analisis`, datos)).data
export const obtenerAnalisis = async (id, signal) => (await api.get(`/imagenes/analisis/${id}`, { signal })).data
export const guardarRevision = async (id, datos) => (await api.post(`/imagenes/analisis/${id}/revision`, datos)).data
