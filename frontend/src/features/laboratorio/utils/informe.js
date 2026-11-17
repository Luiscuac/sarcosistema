import { agruparPorSeccion } from './captura.js'
import { evaluarValor } from './rangoReferencia.js'

/** El informe no trae el tipo de entrada: solo se evalúan valores que son números. */
export function fueraDeRango(parametro) {
  return /^\d[\d.,]*$/.test(String(parametro.valor ?? '').trim())
    && Boolean(evaluarValor(parametro.valor, parametro.rango_referencia, 'decimal'))
}

const normalizar = (texto) => String(texto ?? '').trim().toLowerCase()

// Las plantillas de estudios sueltos usan una sección y un parámetro llamados "Resultado":
// no aportan información y, mostrados, duplican el título.
const esGenerico = (texto, nombreEstudio) => {
  const valor = normalizar(texto)
  return !valor || valor === 'resultado' || valor === 'resultados' || valor === normalizar(nombreEstudio)
}

// Formato libre antiguo: la unidad se capturaba como un parámetro aparte.
const esUnidadLibre = (parametro) => normalizar(parametro.nombre).startsWith('unidad (si aplica)')

/** Integra la "Unidad (si aplica)" del formato libre en el resultado al que pertenece. */
function integrarUnidadLibre(parametros) {
  const unidadLibre = parametros.find(esUnidadLibre)
  const resto = parametros.filter((parametro) => !esUnidadLibre(parametro))
  if (!unidadLibre || resto.length !== 1) return parametros
  return [{ ...resto[0], unidad: resto[0].unidad || unidadLibre.valor }]
}

/**
 * Convierte un estudio en filas de tabla compactas.
 * Un estudio de un solo valor queda en una sola fila con el nombre del estudio;
 * los demás llevan una fila de título y, si corresponde, filas de subsección.
 */
export function filasDeEstudio(resultado) {
  const parametros = integrarUnidadLibre((resultado.parametros ?? []).map((parametro) => ({
    ...parametro,
    seccion: esGenerico(parametro.seccion, resultado.nombre) ? null : parametro.seccion,
  })))
  if (parametros.length === 0) return [{ tipo: 'vacio', nombre: resultado.nombre }]
  if (parametros.length === 1 && !parametros[0].seccion) {
    const [parametro] = parametros
    const nombre = esGenerico(parametro.nombre, resultado.nombre) ? resultado.nombre : `${resultado.nombre} · ${parametro.nombre}`
    return [{ tipo: 'parametro', parametro: { ...parametro, nombre } }]
  }
  const filas = [{ tipo: 'estudio', nombre: resultado.nombre }]
  const secciones = agruparPorSeccion(parametros)
  for (const [seccion, delGrupo] of secciones) {
    const conTitulo = secciones.length > 1 || Boolean(delGrupo[0].seccion)
    if (conTitulo) filas.push({ tipo: 'seccion', nombre: seccion })
    for (const parametro of delGrupo) filas.push({ tipo: 'parametro', parametro, enSeccion: conTitulo })
  }
  return filas
}

/** Agrupa los resultados por área, conservando el orden de aparición. */
export function agruparInformePorArea(resultados = []) {
  const areas = new Map()
  for (const resultado of resultados) {
    if (!areas.has(resultado.categoria)) {
      areas.set(resultado.categoria, { categoria: resultado.categoria, filas: [], observaciones: [], responsables: [] })
    }
    const area = areas.get(resultado.categoria)
    area.filas.push(...filasDeEstudio(resultado))
    const observacion = String(resultado.observaciones ?? '').trim()
    if (observacion && !area.observaciones.includes(observacion)) area.observaciones.push(observacion)
    const responsable = String(resultado.responsable_publicacion ?? '').trim()
    if (responsable && !area.responsables.includes(responsable)) area.responsables.push(responsable)
  }
  return [...areas.values()].map((area) => {
    const parametros = area.filas.filter((fila) => fila.tipo === 'parametro').map((fila) => fila.parametro)
    return {
      ...area,
      tieneUnidad: parametros.some((parametro) => parametro.unidad),
      tieneReferencia: parametros.some((parametro) => parametro.rango_referencia),
    }
  })
}

function estadoRango(parametro) {
  if (!fueraDeRango(parametro)) return null
  return evaluarValor(parametro.valor, parametro.rango_referencia, 'decimal')
}

/**
 * Texto plano para que el médico lo copie a su nota SOAP:
 * una línea por área, "Parámetro: valor unidad", marcando lo que está fuera de rango.
 */
export function resumenParaCopiar(informe, { nombreArea = (codigo) => codigo, nombreMotivo = (codigo) => codigo, fecha = '' } = {}) {
  const lineas = [`Laboratorio ${informe.referencia}${fecha ? ` (${fecha})` : ''}:`]
  for (const area of agruparInformePorArea(informe.resultados)) {
    const valores = []
    for (const fila of area.filas) {
      if (fila.tipo === 'vacio') valores.push(`${fila.nombre}: sin resultado`)
      if (fila.tipo !== 'parametro') continue
      const { parametro } = fila
      const estado = estadoRango(parametro)
      const valor = [String(parametro.valor ?? '').trim(), parametro.unidad].filter(Boolean).join(' ')
      valores.push(`${parametro.nombre}: ${valor}${estado ? ` (${estado})` : ''}`)
    }
    let linea = `- ${nombreArea(area.categoria)}: ${valores.join(', ')}.`
    if (area.observaciones.length) linea += ` Obs.: ${area.observaciones.join(' · ')}`
    lineas.push(linea)
  }
  const noRealizados = informe.estudios_no_realizados ?? []
  if (noRealizados.length) {
    lineas.push(`- No realizados: ${noRealizados.map((estudio) => `${estudio.nombre} (${nombreMotivo(estudio.motivo)})`).join(', ')}.`)
  }
  return lineas.join('\n')
}
