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
    payload[nombre] = limpio ? (numericos.has(nombre) ? Number(limpio) : limpio) : null
  }
  return payload
}

export function confirmarSalida(sucio, confirmar) {
  return !sucio || confirmar('Hay cambios sin guardar. ¿Quieres salir de esta consulta?')
}
