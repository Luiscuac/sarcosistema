import { evaluarValor } from './rangoReferencia.js'

// El parámetro técnico "unidad_reportada" no se captura en pantalla.
export function parametrosVisibles(parametros = []) {
  return parametros.filter((parametro) => parametro.codigo !== 'unidad_reportada')
}

export function agruparPorSeccion(parametros) {
  const secciones = new Map()
  for (const parametro of parametros) {
    const nombre = parametro.seccion || 'Resultado'
    if (!secciones.has(nombre)) secciones.set(nombre, [])
    secciones.get(nombre).push(parametro)
  }
  return [...secciones]
}

const tieneValor = (valor) => String(valor ?? '').trim() !== ''

/** Resumen del avance de captura: cuántos campos hay, faltantes obligatorios y fuera de rango. */
export function resumenCaptura(parametros, valores) {
  const completos = parametros.filter((parametro) => tieneValor(valores[parametro.id])).length
  const faltantes = parametros
    .filter((parametro) => parametro.obligatorio && !tieneValor(valores[parametro.id]))
    .map((parametro) => parametro.nombre)
  const fueraDeRango = parametros.flatMap((parametro) => {
    const estado = evaluarValor(valores[parametro.id], parametro.rango_referencia, parametro.tipo_entrada)
    return estado ? [{ id: parametro.id, nombre: parametro.nombre, valor: valores[parametro.id], estado }] : []
  })
  return { total: parametros.length, completos, faltantes, fueraDeRango }
}

/** Explica, en lenguaje del usuario, por qué todavía no se puede publicar (null si se puede). */
export function motivoPublicacionBloqueada({ hayCambios, responsable, faltantes, sinBorrador }) {
  if (hayCambios) return 'Guarda el borrador antes de publicar: hay cambios sin guardar.'
  if (sinBorrador) return 'Guarda un borrador con los resultados antes de publicar.'
  if (String(responsable ?? '').trim().length < 2) return 'Escribe el nombre del profesional responsable.'
  if (faltantes.length) return `Faltan campos obligatorios: ${faltantes.join(', ')}.`
  return null
}

/** Enter en un campo de resultado lleva al siguiente, como en una planilla. */
export function enfocarSiguienteCampo(evento) {
  const campo = evento.target
  if (evento.key !== 'Enter' || !campo.matches?.('[data-campo-resultado]')) return
  evento.preventDefault()
  const campos = [...evento.currentTarget.querySelectorAll('[data-campo-resultado]:not(:disabled)')]
  campos[campos.indexOf(campo) + 1]?.focus()
}
