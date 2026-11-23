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

/** Avance del registro para ResumenCaptura (mismo formato que Laboratorio): estructuras + datos obligatorios. */
export function resumenRegistro(datos, organos) {
  const faltan = pendientes(datos, organos)
  const total = organos.length + 2 + (['ECO_DOPPLER', 'ECO_PARTES_BLANDAS'].includes(datos.tipo) ? 1 : 0)
  return { total, completos: total - faltan.length, fueraDeRango: [], faltan }
}

/** Por qué todavía no se puede publicar (null si se puede). */
export function motivoBloqueoEco({ faltan, cambio, guardado }) {
  if (faltan.length) return `Para publicar falta completar: ${faltan.join(', ')}.`
  if (cambio) return 'Guarda el borrador antes de publicar.'
  if (!guardado) return 'Guarda el borrador para poder revisarlo y publicarlo.'
  return null
}

/** Acción principal del detalle, como la de Laboratorio. */
export function accionPrincipalEco(estudio) {
  const base = `/ecografia/estudios/${estudio.estudio_id}`
  if (estudio.estado === 'publicado') return { etiqueta: 'Ver informe', ruta: `${base}/informe` }
  if (estudio.informe) return { etiqueta: 'Continuar registro', ruta: `${base}/registro` }
  return { etiqueta: 'Registrar hallazgos', ruta: `${base}/registro` }
}
