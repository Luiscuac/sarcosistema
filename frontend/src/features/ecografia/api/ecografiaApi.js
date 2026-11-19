export {
  listarBandeja,
  obtenerEstudio,
  obtenerArchivoImagen,
  subirInforme,
  publicarInforme,
} from '../../imagenes/api/imagenesApi.js'

export const MODALIDAD_ECOGRAFIA = 'ecografia'

import api from '../../../shared/api/httpClient.js'
export const buscarPacientes = async buscar => (await api.get('/imagenes/ecografia/pacientes', { params: { buscar } })).data
export const obtenerCatalogo = async () => (await api.get('/imagenes/ecografia/catalogo')).data
export const crearSolicitud = async datos => (await api.post('/imagenes/ecografia/solicitudes', datos)).data
export const extraerHallazgosEcografia = async (estudioId, transcripcion, signal) =>
  (await api.post(`/imagenes/estudios/${estudioId}/extraer-ecografia`, { transcripcion },
    { signal, timeout: 200000 })).data
