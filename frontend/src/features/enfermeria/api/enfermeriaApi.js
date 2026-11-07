import api from '../../../shared/api/httpClient.js'

export const buscarPacientesEnfermeria = async (buscar, pagina = 1) =>
  (await api.get('/enfermeria/pacientes', { params: { buscar, pagina } })).data
export const obtenerRegistrosEnfermeria = async (pacienteId) =>
  (await api.get(`/enfermeria/pacientes/${pacienteId}/registros`)).data
export const guardarBorradorEnfermeria = async (pacienteId, datos) =>
  (await api.post(`/enfermeria/pacientes/${pacienteId}/registros`, datos)).data
export const actualizarBorradorEnfermeria = async (registroId, datos) =>
  (await api.put(`/enfermeria/registros/${registroId}`, datos)).data
export const publicarRegistroEnfermeria = async (registroId) =>
  (await api.post(`/enfermeria/registros/${registroId}/publicar`)).data
export const obtenerRegistrosPublicados = async (pacienteId) =>
  (await api.get(`/enfermeria/pacientes/${pacienteId}/publicados`)).data
