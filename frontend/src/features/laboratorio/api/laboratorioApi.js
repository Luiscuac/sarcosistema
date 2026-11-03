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

export async function obtenerSolicitud(solicitudId) {
  const { data } = await httpClient.get(`/laboratorio/solicitudes/${solicitudId}`)
  return data
}

export async function obtenerInformeSolicitud(solicitudId) {
  const { data } = await httpClient.get(`/laboratorio/solicitudes/${solicitudId}/informe`)
  return data
}

export async function recibirMuestraSolicitud(solicitudId, muestra) {
  const { data } = await httpClient.post(`/laboratorio/solicitudes/${solicitudId}/muestras`, muestra)
  return data
}

export async function registrarIncidenciasSolicitud(solicitudId, incidencia) {
  const { data } = await httpClient.post(`/laboratorio/solicitudes/${solicitudId}/incidencias`, incidencia)
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

export async function publicarResultado(estudioId, responsablePublicacion) {
  const { data } = await httpClient.post(`/laboratorio/estudios/${estudioId}/resultado/publicar`, { responsable_publicacion: responsablePublicacion })
  return data
}

export async function guardarBorradorArea(solicitudId, areaCodigo, datos) {
  const { data } = await httpClient.put(`/laboratorio/solicitudes/${solicitudId}/areas/${areaCodigo}/resultados/borrador`, datos)
  return data
}

export async function publicarResultadosArea(solicitudId, areaCodigo, datos) {
  const { data } = await httpClient.post(`/laboratorio/solicitudes/${solicitudId}/areas/${areaCodigo}/resultados/publicar`, datos)
  return data
}
