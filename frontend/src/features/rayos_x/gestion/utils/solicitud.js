function texto(valor) {
  return typeof valor === 'string' ? valor.trim() : ''
}

function mapaCatalogo(catalogo) {
  return new Map((catalogo?.estudios ?? []).map((estudio) => [Number(estudio.id), estudio]))
}

/** Valida la configuracion radiologica de cada estudio antes de enviarla a la API. */
export function erroresDeEstudios(catalogo, valor) {
  if (!Array.isArray(valor) || valor.length === 0) return ['Selecciona al menos un estudio.']
  if (valor.length > 15) return ['Una solicitud puede incluir como máximo 15 estudios.']

  const porId = mapaCatalogo(catalogo)
  const errores = []
  const combinaciones = new Set()

  valor.forEach((seleccion, indice) => {
    const numero = indice + 1
    const estudio = porId.get(Number(seleccion.tipo_estudio_id))
    if (!estudio || estudio.activo === false) {
      errores.push(`Estudio ${numero}: ya no está disponible en el catálogo.`)
      return
    }
    const config = estudio.config ?? {}
    const lateralidad = texto(seleccion.lateralidad) || null
    if (config.requiere_lateralidad && !['derecha', 'izquierda', 'bilateral'].includes(lateralidad)) {
      errores.push(`${estudio.nombre}: selecciona la lateralidad.`)
    }
    if (!config.requiere_lateralidad && lateralidad) {
      errores.push(`${estudio.nombre}: la lateralidad no corresponde a este estudio.`)
    }
    if (lateralidad === 'bilateral' && !config.permite_bilateral) {
      errores.push(`${estudio.nombre}: no admite lateralidad bilateral.`)
    }

    const clave = `${estudio.id}:${lateralidad ?? 'sin_lateralidad'}`
    if (combinaciones.has(clave)) errores.push(`${estudio.nombre}: no puede repetirse con la misma lateralidad.`)
    combinaciones.add(clave)

    const protocolos = config.protocolos ?? []
    const protocolo = texto(seleccion.protocolo)
    if (protocolo && !protocolos.some((item) => item.codigo === protocolo)) {
      errores.push(`${estudio.nombre}: el protocolo seleccionado no es válido.`)
    }

    const permitidas = new Set((config.proyecciones ?? []).map((item) => item.codigo))
    const proyecciones = Array.isArray(seleccion.proyecciones) ? seleccion.proyecciones : []
    if (new Set(proyecciones).size !== proyecciones.length || proyecciones.some((codigo) => !permitidas.has(codigo))) {
      errores.push(`${estudio.nombre}: revisa las proyecciones seleccionadas.`)
    }
    if (!protocolo && proyecciones.length === 0) {
      errores.push(`${estudio.nombre}: elige un protocolo o al menos una proyección.`)
    }
    if (texto(config.detalle_requerido) && !texto(seleccion.detalle_region)) {
      errores.push(`${estudio.nombre}: completa ${config.detalle_requerido.toLocaleLowerCase()}.`)
    }
  })
  return errores
}

export function erroresDeSolicitud({ catalogo, paciente, estudios, pedido }) {
  const errores = []
  if (!paciente?.id) errores.push('Busca y selecciona un paciente antes de continuar.')
  errores.push(...erroresDeEstudios(catalogo, estudios))
  if (pedido?.procedencia === 'este_centro' && !pedido.medico_solicitante_id) {
    errores.push('Selecciona un médico de Sarcobamba de la lista.')
  }
  if (pedido?.procedencia === 'otro_centro') {
    if (!texto(pedido.medico_solicitante_nombre)) errores.push('Escribe el nombre del médico solicitante externo.')
    if (!texto(pedido.establecimiento_solicitante_nombre)) errores.push('Escribe el establecimiento solicitante.')
  }
  return errores
}

export function prepararEstudiosParaApi(estudios) {
  return estudios.map((estudio) => ({
    tipo_estudio_id: Number(estudio.tipo_estudio_id),
    lateralidad: texto(estudio.lateralidad) || null,
    protocolo: texto(estudio.protocolo) || null,
    proyecciones: [...(estudio.proyecciones ?? [])],
    indicacion: texto(estudio.indicacion) || null,
    observaciones: texto(estudio.observaciones) || null,
    detalle_region: texto(estudio.detalle_region) || null,
  }))
}
