import api from '../../../shared/api/httpClient.js'

export const buscarPacientes = async (buscar, pagina = 1) =>
  (await api.get('/consultas/pacientes', { params: { buscar, pagina } })).data
export const obtenerPaciente = async (id) => (await api.get(`/consultas/pacientes/${id}`)).data
export const obtenerHistorial = async (id, pagina = 1) =>
  (await api.get(`/consultas/pacientes/${id}/historial`, { params: { pagina } })).data
export const obtenerConsulta = async (id) => (await api.get(`/consultas/${id}`)).data
export const obtenerSolicitudesLaboratorio = async (pacienteId) =>
  (await api.get(`/laboratorio/pacientes/${pacienteId}/solicitudes`)).data
export const obtenerInformeLaboratorio = async (solicitudId) =>
  (await api.get(`/laboratorio/medicos/solicitudes/${solicitudId}/informe`)).data
export const crearConsulta = async (datos) => (await api.post('/consultas', datos)).data
export const extraerDatosClinicos = async (pacienteId, transcripcion, signal) =>
  (await api.post('/consultas/extraer-datos-clinicos', { paciente_id: Number(pacienteId), transcripcion }, { signal, timeout: 200000 })).data

// Examenes complementarios de imagen (ecografias)
export const obtenerCatalogoImagenes = async () => (await api.get('/consultas/catalogo-imagenes')).data
export const solicitarEcografia = async (pacienteId, tipoEstudioIds, medicoSolicitanteNombre) =>
  (await api.post('/consultas/estudios-imagen', {
    paciente_id: Number(pacienteId), tipo_estudio_ids: tipoEstudioIds.map(Number),
    medico_solicitante_nombre: medicoSolicitanteNombre,
  })).data

/**
 * Descarga autenticada: un <a href> no lleva el token, asi que se pide como blob.
 */
export const descargarArchivoImagen = async (archivoId, nombreOriginal) => {
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
