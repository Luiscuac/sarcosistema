import { describirEdad } from '../../shared/utils/edad.js'

export const fechaLocal = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export const edadEnEstudio = (nacimiento, fecha) => fecha ? describirEdad(nacimiento, new Date(`${fecha}T12:00:00`)) || 'No registrada' : 'No registrada'

export function iniciarDatos(estudio) {
  return estudio.informe?.datos_ecografia || {
    version: 1, tipo: estudio.tipo_estudio_codigo, fecha_estudio: fechaLocal(),
    establecimiento: 'C.S. Sarcobamba', zona: '', conclusion: '',
    observaciones: estudio.informe?.descripcion_texto || '',
    evaluaciones: Object.fromEntries((estudio.organos || []).map(o => [o, ''])),
  }
}

export function agregarArchivos(actuales, nuevos, maximo, conservados = 0) {
  const claves = new Set(actuales.map(f => `${f.name}:${f.size}:${f.lastModified}`))
  const lista = [...actuales]
  for (const f of nuevos) {
    const clave = `${f.name}:${f.size}:${f.lastModified}`
    if (!claves.has(clave)) { lista.push(f); claves.add(clave) }
  }
  if (lista.length + conservados > maximo) throw new Error(`El estudio admite hasta ${maximo} adjuntos. Quita alguno antes de añadir más.`)
  return lista
}

export function pendientes(datos, organos) {
  return [!datos.fecha_estudio && 'Fecha del estudio', ...organos.filter(o => !datos.evaluaciones[o]?.trim()),
    !datos.conclusion.trim() && 'Conclusión',
    ['ECO_DOPPLER', 'ECO_PARTES_BLANDAS'].includes(datos.tipo) && !datos.zona.trim() && 'Zona estudiada'].filter(Boolean)
}
