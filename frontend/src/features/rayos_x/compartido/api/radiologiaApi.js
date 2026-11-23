// Cliente de la API de radiología convencional. Contrato: docs/imagenes/radiologia-api.md
import api from '../../../../shared/api/httpClient.js'

const base = '/imagenes/radiologia'
const datos = async promesa => (await promesa).data

export const obtenerCatalogo = (todos = false) => datos(api.get(`${base}/catalogo`, { params: todos ? { todos: true } : {} }))
export const cambiarEstudioCatalogo = (tipoEstudioId, cambios) => datos(api.patch(`${base}/catalogo/estudios/${tipoEstudioId}`, cambios))

export const buscarPacientes = (termino, signal) => datos(api.get(`${base}/pacientes`, { params: { termino }, signal }))
export const crearPaciente = paciente => datos(api.post(`${base}/pacientes`, paciente))
export const buscarMedicos = (termino, signal) => datos(api.get(`${base}/medicos`, { params: { termino }, signal }))

export const crearSolicitud = solicitud => datos(api.post(`${base}/solicitudes`, solicitud))
export const obtenerSolicitud = (solicitudId, signal) => datos(api.get(`${base}/solicitudes/${solicitudId}`, { signal }))
export const listarEstudios = (vista = 'activos', signal) => datos(api.get(`${base}/estudios`, { params: { vista }, signal }))
export const listarEstudiosPaciente = (pacienteId, signal) => datos(api.get(`${base}/pacientes/${pacienteId}/estudios`, { signal }))
export const obtenerEstudio = (estudioId, signal) => datos(api.get(`${base}/estudios/${estudioId}`, { signal }))

export const guardarAdquisicion = (estudioId, adquisicion) => datos(api.put(`${base}/estudios/${estudioId}/adquisicion`, adquisicion))
export const completarAdquisicion = estudioId => datos(api.post(`${base}/estudios/${estudioId}/adquisicion/completar`))
export const marcarNoRealizado = (estudioId, motivo) => datos(api.post(`${base}/estudios/${estudioId}/no-realizado`, { motivo }))

/** archivos: File[]; proyecciones: códigos en el mismo orden ('' = sin asignar). */
export const subirImagenes = (estudioId, archivos, proyecciones = []) => {
  const formulario = new FormData()
  archivos.forEach((archivo, i) => {
    formulario.append('archivos', archivo, archivo.name)
    formulario.append('proyecciones', proyecciones[i] || '')
  })
  return datos(api.post(`${base}/estudios/${estudioId}/imagenes`, formulario))
}
export const asignarProyeccion = (estudioId, imagenId, proyeccionCodigo) =>
  datos(api.patch(`${base}/estudios/${estudioId}/imagenes/${imagenId}`, { proyeccion_codigo: proyeccionCodigo || null }))
export const retirarImagen = (estudioId, imagenId, motivo) =>
  datos(api.post(`${base}/estudios/${estudioId}/imagenes/${imagenId}/retirar`, { motivo }))

export const previsualizarInforme = (estudioId, contenido, signal) =>
  datos(api.post(`${base}/estudios/${estudioId}/informe/vista-previa`, { contenido }, { signal }))
export const guardarBorradorInforme = (estudioId, borrador) => datos(api.put(`${base}/estudios/${estudioId}/informe/borrador`, borrador))
export const validarInforme = (estudioId, validacion) => datos(api.post(`${base}/estudios/${estudioId}/informe/validar`, validacion))
export const agregarAdenda = (estudioId, adenda) => datos(api.post(`${base}/estudios/${estudioId}/adendas`, adenda))

export const adjuntarInformeExterno = (estudioId, archivo, campos) => {
  const formulario = new FormData()
  formulario.append('archivo', archivo, archivo.name)
  for (const [clave, valor] of Object.entries(campos)) if (valor) formulario.append(clave, valor)
  return datos(api.post(`${base}/estudios/${estudioId}/informes-externos`, formulario))
}
export const retirarInformeExterno = (estudioId, externoId, motivo) =>
  datos(api.post(`${base}/estudios/${estudioId}/informes-externos/${externoId}/retirar`, { motivo }))
export const descargarInformeExterno = (externoId, signal) =>
  datos(api.get(`${base}/informes-externos/${externoId}/archivo`, { responseType: 'blob', signal }))
export const entregarEstudio = (estudioId, entregadoA) => datos(api.post(`${base}/estudios/${estudioId}/entregar`, { entregado_a: entregadoA }))

// Binarios de imagen (rutas existentes). `vista` devuelve PNG de 8 bits y sirve también para DICOM.
export const obtenerVistaImagen = (archivoId, signal) => datos(api.get(`/imagenes/archivos/${archivoId}/vista`, { responseType: 'blob', signal }))
export const obtenerArchivoOriginal = (archivoId, signal) => datos(api.get(`/imagenes/archivos/${archivoId}`, { responseType: 'blob', signal }))

export const pendientesDeError = error => error?.response?.data?.detail?.pendientes || []
