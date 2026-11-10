import api from '../../../shared/api/httpClient.js'

export const obtenerInformeRecetasFarmacia = async () => (await api.get('/enfermeria/farmacia/recetas')).data
