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

export const NOMBRES_HALLAZGOS = {
  Atelectasis: 'Atelectasia', Consolidation: 'Consolidación', Infiltration: 'Infiltrado', Pneumothorax: 'Neumotórax',
  Edema: 'Edema pulmonar', Emphysema: 'Enfisema', Fibrosis: 'Fibrosis', Effusion: 'Derrame pleural', Pneumonia: 'Neumonía',
  Pleural_Thickening: 'Engrosamiento pleural', Cardiomegaly: 'Cardiomegalia', Nodule: 'Nódulo', Mass: 'Masa', Hernia: 'Hernia',
  'Lung Lesion': 'Lesión pulmonar', Fracture: 'Fractura', 'Lung Opacity': 'Opacidad pulmonar',
  'Enlarged Cardiomediastinum': 'Ensanchamiento cardiomediastínico',
}
export const nombreHallazgo = nombre => NOMBRES_HALLAZGOS[nombre] || nombre

export const NIVELES_TRIAJE = {
  alta: { texto: 'Revisar primero', clase: 'alta' },
  media: { texto: 'Prioridad media', clase: 'media' },
  baja: { texto: 'Prioridad baja', clase: 'baja' },
}

/** Urgencia clínica primero; luego índice visual (mayor primero, sin triaje al final); luego antigüedad. */
export function ordenarBandeja(estudios, modo = 'prioridad') {
  const fecha = e => new Date(e.fecha_solicitud).getTime()
  return [...estudios].sort((a, b) => {
    const urgencia = (b.prioridad === 'urgente') - (a.prioridad === 'urgente')
    if (urgencia) return urgencia
    if (modo === 'prioridad') {
      const ia = a.triaje?.indice ?? -1
      const ib = b.triaje?.indice ?? -1
      if (ia !== ib) return ib - ia
    }
    return fecha(a) - fecha(b)
  })
}

export const triajeEnProceso = estudios => (estudios || []).some(e => e.triaje?.estado === 'en_proceso')

/** Adapta resultados antiguos (solo 3 categorías) y nuevos (18 + índice + mapas). */
export function hallazgosDeVision(vision) {
  const todas = vision?.all_findings?.length
    ? vision.all_findings
    : [...(vision?.findings || [])].sort((a, b) => b.score - a.score).map(h => ({ ...h, above_operating_point: h.score >= 0.5 }))
  const principales = ['Consolidation', 'Effusion', 'Cardiomegaly']
    .map(n => todas.find(h => h.name === n)).filter(Boolean)
  return { todas, principales, completo: Boolean(vision?.all_findings?.length) }
}

export function mapasDisponibles(vision) {
  const mapas = vision?.mapas_calor?.mapas || {}
  return Object.keys(mapas).map(clave => ({ clave, etiqueta: clave === 'indice_pulmonar' ? 'Índice pulmonar' : nombreHallazgo(clave) }))
}

const ORDEN_AVISOS = { discrepancia: 0, posible_omision: 1, coincidencia: 2 }

/** Avisos de la comparación, discrepancias primero. Compatible con resultados antiguos sin `tipo`. */
export function avisosDeFusion(fusion) {
  const con = (lista, tipo) => (lista || []).map(a => ({ ...a, tipo: a.tipo || tipo }))
  return [...con(fusion?.discrepancias, 'discrepancia'), ...con(fusion?.posibles_omisiones, 'posible_omision'), ...con(fusion?.coincidencias, 'coincidencia')]
    .sort((a, b) => ORDEN_AVISOS[a.tipo] - ORDEN_AVISOS[b.tipo] || (b.score ?? 0) - (a.score ?? 0))
}

export const mencionesDelInforme = fusion => Object.entries(fusion?.informe || {})
  .filter(([, d]) => d.estado !== 'no_mencionado')
  .map(([nombre, d]) => ({ nombre, estado: d.estado, evidencia: d.evidencia || [] }))

export const porcentaje = valor => (typeof valor === 'number' && Number.isFinite(valor) ? `${Math.round(valor * 100)} %` : '—')

/** Lectura del médico en la revisión: '' (no indicada), 'si' o 'no' -> true/false/null. */
export const lecturaAnormal = valor => (valor === 'si' ? true : valor === 'no' ? false : null)

/** Sugerencias del modelo: las señales más fuertes primero; el resto son señales débiles (falsas alarmas frecuentes). */
export const MAX_SUGERENCIAS = 3
export function sugerenciasDeVision(vision) {
  const { todas } = hallazgosDeVision(vision)
  const sobreCorte = todas.filter(h => h.above_operating_point).sort((a, b) => b.score - a.score)
  return {
    principales: sobreCorte.slice(0, MAX_SUGERENCIAS),
    debiles: sobreCorte.slice(MAX_SUGERENCIAS),
    sinSenal: todas.filter(h => !h.above_operating_point).sort((a, b) => b.score - a.score),
  }
}

/** Nivel de señal en lenguaje simple a partir del score normalizado (0,5 = punto de corte del modelo). */
export function nivelSenal(score) {
  if (typeof score !== 'number' || !Number.isFinite(score)) return { clave: 'sin_dato', texto: 'Sin dato' }
  if (score >= 0.75) return { clave: 'alta', texto: 'Señal alta' }
  if (score >= 0.55) return { clave: 'moderada', texto: 'Señal moderada' }
  // Justo sobre el punto de corte: en radiografías normales aparece con frecuencia; es ruido del modelo.
  if (score >= 0.5) return { clave: 'limite', texto: 'Señal límite' }
  return { clave: 'baja', texto: 'Sin señal relevante' }
}

/** Veredicto orientativo para el médico según el nivel de prioridad del índice y los hallazgos destacados. */
export const VEREDICTOS = {
  alta: { titulo: 'Revisar con prioridad', texto: 'El modelo encuentra señales que conviene revisar pronto en la imagen.' },
  media: { titulo: 'Revisar con atención', texto: 'El modelo encuentra algunas señales; revísalas junto con el informe.' },
  baja: { titulo: 'Sin señales importantes', texto: 'El modelo no encuentra señales relevantes. Esto no descarta enfermedad.' },
}

export const DECISIONES = {
  aceptada_como_propuesta: 'Aceptada como propuesta',
  corregida: 'Corregida',
  rechazada: 'Rechazada',
}
