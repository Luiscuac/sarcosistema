import httpClient from '../../../shared/api/httpClient.js'

export async function crearExamen(examen) {
  const { data } = await httpClient.post('/examenes', examen)
  return data
}

export async function listarExamenes() {
  const { data } = await httpClient.get('/examenes')
  return data
}

export async function obtenerExamen(examenId) {
  const { data } = await httpClient.get(`/examenes/${examenId}`)
  return data
}
