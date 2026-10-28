const FORMATO = { day: '2-digit', month: '2-digit', year: 'numeric' }

/**
 * Fecha en formato dd/mm/aaaa.
 * Una fecha de calendario ("1990-01-05") se interpreta como día local: si se
 * parseara como instante UTC, en zonas horarias negativas se mostraría el día anterior.
 */
export function formatearFecha(fechaISO) {
  const valor = String(fechaISO ?? '')
  const soloFecha = valor.split('T')[0]
  if (/^\d{4}-\d{2}-\d{2}$/.test(soloFecha)) {
    const [anio, mes, dia] = soloFecha.split('-')
    return new Date(Number(anio), Number(mes) - 1, Number(dia)).toLocaleDateString('es-BO', FORMATO)
  }
  return new Date(valor).toLocaleDateString('es-BO', FORMATO)
}
