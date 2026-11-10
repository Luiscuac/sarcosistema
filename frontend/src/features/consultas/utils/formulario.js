import { leerNumero, leerPresion } from '../../enfermeria/utils/signosVitales.js'

export const grupos = [
  { titulo: 'Signos vitales y antropometría', campos: [
    ['peso_kg', 'Peso (kg)'], ['talla_cm', 'Talla (cm)'], ['temperatura_c', 'Temperatura (°C)'],
    ['frecuencia_cardiaca', 'Frecuencia cardíaca (lat/min)'], ['frecuencia_respiratoria', 'Frecuencia respiratoria (resp/min)'],
    ['presion_sistolica', 'Presión sistólica (mmHg)'], ['presion_diastolica', 'Presión diastólica (mmHg)'],
    ['saturacion_oxigeno', 'Saturación de oxígeno (%)'],
  ], numerico: true },
  { titulo: 'S · Subjetivo', campos: [
    ['motivo_consulta', 'Motivo de consulta *'], ['sintomas', 'Síntomas'], ['enfermedad_actual', 'Enfermedad actual'], ['antecedentes', 'Antecedentes relevantes'],
  ] },
  { titulo: 'O · Objetivo', campos: [
    ['examen_fisico', 'Examen físico'], ['hallazgos', 'Hallazgos clínicos'], ['observaciones', 'Observaciones'],
  ] },
  { titulo: 'A · Análisis', campos: [
    ['evaluacion_clinica', 'Evaluación clínica'], ['diagnostico_principal', 'Diagnóstico principal *'],
    ['diagnosticos_secundarios', 'Diagnósticos secundarios'],
  ] },
  { titulo: 'P · Plan de acción', campos: [
    ['tratamiento', 'Tratamiento'], ['medicamentos', 'Medicamentos indicados (texto)'],
    ['indicaciones', 'Indicaciones médicas'], ['estudios_solicitados', 'Estudios complementarios solicitados'],
    ['referencias', 'Referencias y contrarreferencias'], ['recomendaciones', 'Recomendaciones'],
    ['plan_seguimiento', 'Seguimiento o próxima revisión'],
  ] },
]

const numericos = new Set(grupos[0].campos.map(([nombre]) => nombre))
const permitidos = new Set(grupos.flatMap(({ campos }) => campos.map(([nombre]) => nombre)))

export function calcularImc(peso, talla) {
  const kg = Number(peso)
  const cm = Number(talla)
  return peso !== '' && talla !== '' && kg > 0 && cm > 0 && Number.isFinite(kg) && Number.isFinite(cm)
    ? Math.round(kg / (cm / 100) ** 2 * 10) / 10 : null
}

export function formularioAPayload(formulario, pacienteId, clave) {
  const payload = { paciente_id: Number(pacienteId), clave_idempotencia: clave }
  for (const [nombre, valor] of Object.entries(formulario)) {
    if (!permitidos.has(nombre)) continue
    const limpio = String(valor ?? '').trim()
    // leerNumero acepta coma decimal ("36,5"); Number("36,5") daba NaN.
    payload[nombre] = limpio ? (numericos.has(nombre) ? leerNumero(limpio) : limpio) : null
  }
  return payload
}

export function confirmarSalida(sucio, confirmar) {
  return !sucio || confirmar('Hay cambios sin guardar. ¿Quieres salir de esta consulta?')
}

/** Formulario vacío de la consulta; `presion` es el campo visible "120/80" (no se envía). */
export const formularioInicial = () => ({
  ...Object.fromEntries(grupos.flatMap((grupo) => grupo.campos.map(([campo]) => [campo, '']))),
  presion: '',
})

/** Escribir "120/80" actualiza también sistólica y diastólica (vacías mientras no sea válida). */
export function conPresion(form, texto) {
  const presion = leerPresion(texto)
  const valida = presion && !presion.error
  return { ...form, presion: texto,
    presion_sistolica: valida ? String(presion.sistolica) : '',
    presion_diastolica: valida ? String(presion.diastolica) : '' }
}

/** Tras aplicar sistólica o diastólica (p. ej. desde la IA), rehace el texto visible "120/80". */
export function sincronizarPresion(form) {
  const s = String(form.presion_sistolica ?? '').trim()
  const d = String(form.presion_diastolica ?? '').trim()
  return { ...form, presion: s || d ? `${s}/${d}` : '' }
}

/** Campos de la admisión de enfermería que existen en la consulta (mismo nombre). */
export const CAMPOS_DE_ENFERMERIA = [
  'peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca', 'frecuencia_respiratoria',
  'presion_sistolica', 'presion_diastolica', 'saturacion_oxigeno', 'motivo_consulta', 'sintomas',
]

/**
 * Copia la admisión publicada por enfermería a la consulta, solo en campos vacíos:
 * lo que el médico ya escribió no se pisa. Devuelve los campos copiados y los conservados.
 */
export function transferirEnfermeria(form, registro) {
  const nuevo = { ...form }
  const copiados = []
  const conservados = []
  for (const campo of CAMPOS_DE_ENFERMERIA) {
    const valor = registro?.[campo]
    if (valor == null || String(valor).trim() === '') continue
    if (String(form[campo] ?? '').trim() !== '') {
      if (String(form[campo]).trim() !== String(valor).trim()) conservados.push(campo)
      continue
    }
    nuevo[campo] = String(valor)
    copiados.push(campo)
  }
  return { form: sincronizarPresion(nuevo), copiados, conservados }
}
