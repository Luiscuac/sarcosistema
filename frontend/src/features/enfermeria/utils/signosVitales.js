// Lógica de la admisión de enfermería, sin interfaz para poder probarla con node:test.
// Los límites "válidos" copian AdmisionRequest del backend (app/enfermeria/presentation/schemas.py);
// los "habituales" son referencias de adulto que solo sirven para resaltar valores: nunca bloquean.

export const TEXTOS = [
  ['motivo_consulta', 'Motivo referido por el paciente'],
  ['sintomas', 'Síntomas referidos'],
  ['observaciones_enfermeria', 'Observaciones de enfermería'],
]

/** campo: etiqueta, unidad, límites válidos (backend) y rango habitual de adulto (solo aviso). */
export const MEDICIONES = {
  peso_kg: { etiqueta: 'Peso', unidad: 'kg', minExclusivo: 0, max: 500 },
  talla_cm: { etiqueta: 'Talla', unidad: 'cm', minExclusivo: 0, max: 300 },
  temperatura_c: { etiqueta: 'Temperatura', unidad: '°C', min: 25, max: 45, habitual: [35, 37.9], alto: 'Fiebre', bajo: 'Hipotermia' },
  frecuencia_cardiaca: { etiqueta: 'Frecuencia cardíaca', unidad: 'lpm', min: 1, max: 300, habitual: [60, 100], adulto: true },
  frecuencia_respiratoria: { etiqueta: 'Frecuencia respiratoria', unidad: 'rpm', min: 1, max: 100, habitual: [12, 20], adulto: true },
  saturacion_oxigeno: { etiqueta: 'Saturación de oxígeno', unidad: '%', min: 1, max: 100, habitual: [92, 100], bajo: 'Saturación baja' },
}

export const GRUPOS = [
  { titulo: 'Antropometría', campos: ['peso_kg', 'talla_cm'] },
  { titulo: 'Signos vitales', campos: ['temperatura_c', 'frecuencia_cardiaca', 'frecuencia_respiratoria', 'presion', 'saturacion_oxigeno'] },
]

export const PRESION = { etiqueta: 'Presión arterial', unidad: 'mmHg', ejemplo: '120/80' }

export const FORMULARIO_VACIO = {
  ...Object.fromEntries(TEXTOS.map(([campo]) => [campo, ''])),
  ...Object.fromEntries(Object.keys(MEDICIONES).map((campo) => [campo, ''])),
  presion: '',
  dolor_escala: '',
}

/** "36,5" y "36.5" -> 36.5; texto vacío -> null; cualquier otra cosa -> NaN. */
export function leerNumero(texto) {
  const limpio = String(texto ?? '').trim().replace(',', '.')
  if (!limpio) return null
  return /^\d+(\.\d+)?$/.test(limpio) ? Number(limpio) : Number.NaN
}

/** "120/80" -> { sistolica: 120, diastolica: 80 }; vacío -> null; mal escrito -> { error }. */
export function leerPresion(texto) {
  const limpio = String(texto ?? '').trim()
  if (!limpio) return null
  const partes = limpio.match(/^(\d{1,3})\s*\/\s*(\d{1,3})$/)
  if (!partes) return { error: 'Escribe la presión como sistólica/diastólica, por ejemplo 120/80.' }
  const sistolica = Number(partes[1])
  const diastolica = Number(partes[2])
  if (sistolica < 1 || sistolica > 300) return { error: 'La sistólica debe estar entre 1 y 300 mmHg.' }
  if (diastolica < 1 || diastolica > 200) return { error: 'La diastólica debe estar entre 1 y 200 mmHg.' }
  if (sistolica <= diastolica) return { error: 'La sistólica debe ser mayor que la diastólica.' }
  return { sistolica, diastolica }
}

/** Mensaje de error del campo o null. Repite en pantalla las reglas del backend. */
export function errorDeCampo(campo, texto) {
  if (campo === 'presion') return leerPresion(texto)?.error ?? null
  if (campo === 'dolor_escala') return null
  const definicion = MEDICIONES[campo]
  if (!definicion) return null
  const valor = leerNumero(texto)
  if (valor === null) return null
  if (Number.isNaN(valor)) return 'Escribe solo números (puedes usar coma decimal).'
  if (definicion.minExclusivo !== undefined && valor <= definicion.minExclusivo) return `Debe ser mayor que ${definicion.minExclusivo} ${definicion.unidad}.`
  if (definicion.min !== undefined && valor < definicion.min) return `Debe ser al menos ${definicion.min} ${definicion.unidad}.`
  if (valor > definicion.max) return `No puede superar ${definicion.max} ${definicion.unidad}.`
  return null
}

/**
 * Aviso clínico para resaltar (no bloquea): { nivel: 'alto' | 'bajo', texto } o null.
 * FC y FR usan referencias de adulto: en menores de 18 años no se marcan.
 */
export function avisoDeCampo(campo, texto, edad = null) {
  if (errorDeCampo(campo, texto)) return null
  if (campo === 'presion') {
    const presion = leerPresion(texto)
    if (!presion) return null
    if (edad !== null && edad < 18) return null
    if (presion.sistolica >= 140 || presion.diastolica >= 90) return { nivel: 'alto', texto: 'Presión elevada' }
    if (presion.sistolica < 90 || presion.diastolica < 60) return { nivel: 'bajo', texto: 'Presión baja' }
    return null
  }
  if (campo === 'dolor_escala') {
    const dolor = leerNumero(texto)
    return dolor !== null && dolor >= 7 ? { nivel: 'alto', texto: 'Dolor intenso' } : null
  }
  const definicion = MEDICIONES[campo]
  const valor = leerNumero(texto)
  if (!definicion?.habitual || valor === null) return null
  if (definicion.adulto && edad !== null && edad < 18) return null
  const [minimo, maximo] = definicion.habitual
  if (valor > maximo) return { nivel: 'alto', texto: definicion.alto ?? 'Sobre lo habitual' }
  if (valor < minimo) return { nivel: 'bajo', texto: definicion.bajo ?? 'Bajo lo habitual' }
  return null
}

/** IMC con un decimal, o null si falta peso o talla válidos. */
export function calcularImc(pesoTexto, tallaTexto) {
  const peso = leerNumero(pesoTexto)
  const talla = leerNumero(tallaTexto)
  if (!peso || !talla || Number.isNaN(peso) || Number.isNaN(talla)) return null
  if (errorDeCampo('peso_kg', pesoTexto) || errorDeCampo('talla_cm', tallaTexto)) return null
  const metros = talla / 100
  return Math.round((peso / (metros * metros)) * 10) / 10
}

/** Campos con error, en el orden del formulario. */
export function erroresDelFormulario(form) {
  return [...Object.keys(MEDICIONES), 'presion']
    .map((campo) => [campo, errorDeCampo(campo, form[campo])])
    .filter(([, error]) => error)
}

export const formularioVacio = (form) => Object.values(form).every((valor) => String(valor ?? '').trim() === '')

/** Registro del backend -> estado del formulario (textos). */
export function formularioDesdeRegistro(registro) {
  const texto = (valor) => (valor == null ? '' : String(valor))
  return {
    ...Object.fromEntries(TEXTOS.map(([campo]) => [campo, texto(registro?.[campo])])),
    ...Object.fromEntries(Object.keys(MEDICIONES).map((campo) => [campo, texto(registro?.[campo])])),
    presion: registro?.presion_sistolica != null && registro?.presion_diastolica != null
      ? `${registro.presion_sistolica}/${registro.presion_diastolica}` : '',
    dolor_escala: texto(registro?.dolor_escala),
  }
}

/** Estado del formulario -> cuerpo que espera AdmisionRequest. Supone un formulario sin errores. */
export function cuerpoDesdeFormulario(form) {
  const presion = leerPresion(form.presion)
  return {
    ...Object.fromEntries(TEXTOS.map(([campo]) => [campo, form[campo].trim() || null])),
    ...Object.fromEntries(Object.keys(MEDICIONES).map((campo) => [campo, leerNumero(form[campo])])),
    presion_sistolica: presion?.sistolica ?? null,
    presion_diastolica: presion?.diastolica ?? null,
    dolor_escala: leerNumero(form.dolor_escala),
  }
}

/** Líneas legibles de lo que se va a guardar o publicar, en el orden del formulario. */
export function resumenDelFormulario(form) {
  const lineas = []
  for (const campo of ['peso_kg', 'talla_cm', 'temperatura_c', 'frecuencia_cardiaca', 'frecuencia_respiratoria', 'presion', 'saturacion_oxigeno']) {
    const valor = String(form[campo] ?? '').trim()
    if (!valor) continue
    const definicion = campo === 'presion' ? PRESION : MEDICIONES[campo]
    lineas.push({ campo, etiqueta: definicion.etiqueta, valor: `${valor.replace('.', ',')} ${definicion.unidad}` })
  }
  const imc = calcularImc(form.peso_kg, form.talla_cm)
  if (imc !== null) lineas.splice(2, 0, { campo: 'imc', etiqueta: 'IMC (calculado)', valor: String(imc).replace('.', ',') })
  if (String(form.dolor_escala).trim()) lineas.push({ campo: 'dolor_escala', etiqueta: 'Dolor', valor: `${form.dolor_escala} de 10` })
  for (const [campo, etiqueta] of TEXTOS) {
    if (form[campo].trim()) lineas.push({ campo, etiqueta, valor: form[campo].trim() })
  }
  return lineas
}
