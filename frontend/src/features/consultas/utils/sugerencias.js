import { grupos } from './formulario.js'

const permitidos = new Set(grupos.flatMap(g => g.campos.map(([campo]) => campo)))

export function aplicarSugerencia(form, item, confirmado = false) {
  const anterior = String(form[item.campo] ?? '')
  if (!permitidos.has(item.campo) || item.ambiguo) return { form, aplicada: false }
  if (anterior.trim() && anterior !== String(item.valor) && !confirmado) {
    return { form, aplicada: false, requiereConfirmacion: true, anterior }
  }
  return { form: { ...form, [item.campo]: String(item.valor) }, aplicada: true, anterior }
}

export function deshacerSugerencia(form, item, revisionActual) {
  if (item.revisionAplicacion !== undefined && item.revisionAplicacion !== revisionActual) return form
  return String(form[item.campo] ?? '') === String(item.valor)
    ? { ...form, [item.campo]: item.anterior ?? '' } : form
}
