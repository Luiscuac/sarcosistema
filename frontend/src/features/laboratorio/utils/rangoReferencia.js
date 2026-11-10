// Interpreta los rangos de referencia transcritos como texto (D-9) solo para
// resaltar valores en pantalla. Nunca bloquea: un valor fuera de rango puede ser real.

const NUMERO = String.raw`\d[\d.,]*`

const PATRONES = [
  { regex: new RegExp(String.raw`^(${NUMERO})\s*(?:a|-|–)\s*(${NUMERO})`, 'i'), crear: ([a, b]) => ({ min: a, max: b }) },
  { regex: new RegExp(String.raw`^(?:hasta|menor\s+a|<|≤)\s*(${NUMERO})`, 'i'), crear: ([a]) => ({ min: null, max: a }) },
  { regex: new RegExp(String.raw`^(?:mayor\s+a|>|≥)\s*(${NUMERO})`, 'i'), crear: ([a]) => ({ min: a, max: null }) },
]

/** "3,500,000" usa comas de miles; "0,5" usa coma decimal; "1.010" usa punto decimal. */
export function interpretarNumero(texto) {
  const limpio = String(texto ?? '').trim().replace(/[.,]$/, '')
  if (!limpio) return null
  const normalizado = /^\d{1,3}(,\d{3})+(\.\d+)?$/.test(limpio)
    ? limpio.replaceAll(',', '')
    : limpio.replace(',', '.')
  if (!/^\d+(\.\d+)?$/.test(normalizado)) return null
  return Number(normalizado)
}

export function interpretarRango(texto) {
  const valor = String(texto ?? '').trim()
  for (const { regex, crear } of PATRONES) {
    const coincidencia = valor.match(regex)
    if (!coincidencia) continue
    const { min, max } = crear(coincidencia.slice(1))
    const rango = { min: min === null ? null : interpretarNumero(min), max: max === null ? null : interpretarNumero(max) }
    const valido = (min === null || rango.min !== null) && (max === null || rango.max !== null)
      && (rango.min === null || rango.max === null || rango.min <= rango.max)
    return valido ? rango : null
  }
  return null
}

/** Devuelve 'bajo', 'alto' o null (dentro de rango, sin rango interpretable o sin valor). */
export function evaluarValor(valor, textoRango, tipoEntrada) {
  if (!['decimal', 'entero'].includes(tipoEntrada)) return null
  const rango = interpretarRango(textoRango)
  const numero = interpretarNumero(valor)
  if (!rango || numero === null) return null
  if (rango.min !== null && numero < rango.min) return 'bajo'
  if (rango.max !== null && numero > rango.max) return 'alto'
  return null
}

export const ETIQUETA_FUERA_DE_RANGO = { bajo: 'Bajo el rango', alto: 'Sobre el rango' }
