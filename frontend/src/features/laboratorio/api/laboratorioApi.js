import httpClient from '../../../shared/api/httpClient.js'

export async function listarEstudiosCatalogo() {
  const { data } = await httpClient.get('/laboratorio/catalogo/estudios')
  return data
}

export async function listarExamenes() {
  const { data } = await httpClient.get('/laboratorio/estudios/pendientes')
  return data
}

export async function listarResultadosPublicados() {
  const { data } = await httpClient.get('/laboratorio/estudios/publicados')
  return data
}

export async function buscarPacientes(termino) {
  const { data } = await httpClient.get('/laboratorio/pacientes', { params: { termino } })
  return data
}

export async function crearPaciente(paciente) {
  const { data } = await httpClient.post('/laboratorio/pacientes', paciente)
  return data
}

export async function crearSolicitud(solicitud) {
  const { data } = await httpClient.post('/laboratorio/solicitudes', solicitud)
  return data
}

export async function recibirMuestraSolicitud(solicitudId, muestra) {
  const { data } = await httpClient.post(`/laboratorio/solicitudes/${solicitudId}/muestras`, muestra)
  return data
}

export async function obtenerExamen(estudioId) {
  const { data } = await httpClient.get(`/laboratorio/estudios/${estudioId}/resultado`)
  return data
}

export async function guardarBorrador(estudioId, resultado) {
  const { data } = await httpClient.put(`/laboratorio/estudios/${estudioId}/resultado/borrador`, resultado)
  return data
}

export async function publicarResultado(estudioId) {
  const { data } = await httpClient.post(`/laboratorio/estudios/${estudioId}/resultado/publicar`)
  return data
}
