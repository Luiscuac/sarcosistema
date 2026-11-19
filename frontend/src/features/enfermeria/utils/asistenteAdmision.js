export const ETIQUETAS_PROPUESA_ADMISION = {
  motivo_consulta: 'Motivo referido',
  sintomas: 'Síntomas',
  observaciones_enfermeria: 'Observaciones de enfermería',
  observaciones: 'Observaciones de enfermería',
  peso_kg: 'Peso',
  talla_cm: 'Talla',
  temperatura_c: 'Temperatura',
  frecuencia_cardiaca: 'Frecuencia cardíaca',
  frecuencia_respiratoria: 'Frecuencia respiratoria',
  presion_sistolica: 'Presión sistólica',
  presion_diastolica: 'Presión diastólica',
  saturacion_oxigeno: 'Saturación de oxígeno',
  dolor_escala: 'Escala de dolor',
}

export function textoPropuesta(item) {
  if (item.campo === 'presion_sistolica' || item.campo === 'presion_diastolica') {
    return `${item.valor} mmHg`
  }
  const unidades = {
    peso_kg: 'kg',
    talla_cm: 'cm',
    temperatura_c: '°C',
    frecuencia_cardiaca: 'lpm',
    frecuencia_respiratoria: 'rpm',
    saturacion_oxigeno: '%',
  }
  if (item.campo === 'dolor_escala') return `${item.valor} de 10`
  return unidades[item.campo] ? `${item.valor} ${unidades[item.campo]}` : String(item.valor)
}

export function parchesAdmision(item, formActual) {
  const campo = item.campo
  if (campo === 'presion_sistolica' || campo === 'presion_diastolica') {
    const partes = String(formActual.presion || '').split('/')
    let sistolica = partes[0]?.trim() || ''
    let diastolica = partes[1]?.trim() || ''
    if (campo === 'presion_sistolica') sistolica = String(item.valor)
    if (campo === 'presion_diastolica') diastolica = String(item.valor)
    return { presion: sistolica && diastolica ? `${sistolica}/${diastolica}` : '' }
  }
  if (campo === 'observaciones') return { observaciones_enfermeria: String(item.valor) }
  if (Object.prototype.hasOwnProperty.call(formActual, campo)) {
    return { [campo]: String(item.valor) }
  }
  return null
}
