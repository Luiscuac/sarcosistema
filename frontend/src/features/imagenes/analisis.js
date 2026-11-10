export const enProceso = estado => ['en_cola', 'procesando'].includes(estado)

export function snapshotCompatible(analisis, detalle) {
  return Boolean(analisis && detalle?.archivo && analisis.informe_id === detalle.informe_id &&
    analisis.archivo_id === detalle.archivo.id && analisis.archivo_sha256 === detalle.archivo.hash_sha256 &&
    analisis.informe_texto === detalle.informe_texto)
}

export const revisionVigente = (base, actual) => base !== null && base === actual

export function validarRevision(decision, motivo, correccion) {
  return decision === 'aceptada_como_propuesta' ||
    (decision === 'rechazada' && Boolean(motivo.trim())) ||
    (decision === 'corregida' && Boolean(motivo.trim() && correccion.trim()))
}

export function mensajeError(error) {
  const estado = error?.response?.status
  if (estado === 401 || estado === 403) return 'Tu sesión no tiene permiso para esta operación.'
  if (estado === 404) return 'El estudio, archivo o análisis no está disponible para tu cuenta.'
  if (estado === 409) return 'Los datos cambiaron o hay un análisis activo; recarga antes de reintentar.'
  if (estado === 503) return 'La asistencia local no está habilitada o no está disponible. Puedes consultar el informe.'
  if (estado === 422) return 'Revisa la confirmación de tórax frontal y los datos obligatorios.'
  if (!error?.response) return 'No se pudo conectar con el servidor local.'
  return 'No se pudo completar la operación; no se modificó el informe clínico.'
}

export const erroresAnalisis = {
  RecursosInsuficientes: 'Memoria libre insuficiente. Libera recursos antes de solicitar otro análisis.',
  ModeloNoPreparado: 'Faltan pesos locales preparados. No se descargan durante el análisis.',
  TiempoAgotado: 'El modelo superó el tiempo máximo y se detuvo.',
  InferenciaOcupada: 'Otro modelo local está en ejecución. Reintenta cuando termine.',
  ImagenNoValida: 'La imagen no cumple el formato o preprocesamiento admitido.',
  snapshot_obsoleto: 'El informe o archivo cambió o no supera la validación local. Recarga el estudio.',
  reinicio: 'El servidor se reinició; solicita nuevamente el análisis.',
}
