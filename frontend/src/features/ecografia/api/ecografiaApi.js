import api from '../../../shared/api/httpClient.js'

export const buscarPacientes = async buscar => (await api.get('/imagenes/ecografia/pacientes', { params: { buscar } })).data
export const obtenerCatalogo = async () => (await api.get('/imagenes/ecografia/catalogo')).data
export const crearSolicitud = async datos => (await api.post('/imagenes/ecografia/solicitudes', datos)).data

export const listarBandeja = async () => (await api.get('/imagenes/bandeja')).data
export const obtenerEstudio = async id => (await api.get(`/imagenes/estudios/${id}`)).data
export const obtenerArchivoImagen = async archivoId =>
  (await api.get(`/imagenes/archivos/${archivoId}`, { responseType: 'blob' })).data

export const subirInforme = async (estudioId, descripcion, archivos, opciones = {}) => {
  const datos = new FormData()
  datos.append('descripcion', descripcion)
  for (const archivo of archivos) datos.append('archivos', archivo, archivo.name)
  if (opciones.datos) datos.append('datos_ecografia', JSON.stringify(opciones.datos))
  if (opciones.conservar) datos.append('conservar_archivos', JSON.stringify(opciones.conservar))
  return (await api.post(`/imagenes/estudios/${estudioId}/informes`, datos)).data
}

export const publicarInforme = async estudioId =>
  (await api.post(`/imagenes/estudios/${estudioId}/informes/publicar`)).data

// DICOM no se ve en el navegador: el servidor genera una vista PNG local con los mismos permisos.
export const esImagenVisible = mime => mime.startsWith('image/') || mime === 'application/dicom'
export const obtenerImagenVisible = async archivo => (archivo.mime_type === 'application/dicom'
  ? (await api.get(`/imagenes/archivos/${archivo.id}/vista`, { responseType: 'blob' })).data
  : obtenerArchivoImagen(archivo.id))
