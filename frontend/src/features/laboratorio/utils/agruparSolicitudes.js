export const categoriasLaboratorio = [
  { codigo: 'hematologia', nombre: 'Hematología' },
  { codigo: 'bioquimica', nombre: 'Bioquímica' },
  { codigo: 'serologia', nombre: 'Serología' },
  { codigo: 'copro_orina', nombre: 'Copro y orina' },
]

export function agruparSolicitudes(estudios) {
  const porSolicitud = new Map()
  for (const estudio of estudios) {
    let solicitud = porSolicitud.get(estudio.solicitud_id)
    if (!solicitud) {
      solicitud = {
        id: estudio.solicitud_id,
        referencia: estudio.referencia_solicitud,
        paciente_id: estudio.paciente_id,
        paciente_nombre: estudio.paciente_nombre,
        fecha_solicitud: estudio.fecha_solicitud,
        prioridad: estudio.prioridad,
        estudios: [],
      }
      porSolicitud.set(estudio.solicitud_id, solicitud)
    }
    solicitud.estudios.push(estudio)
  }
  return [...porSolicitud.values()]
}

export function agruparPorCategoria(estudios) {
  const categorias = categoriasLaboratorio.map((categoria) => ({
    ...categoria,
    estudios: estudios.filter((estudio) => estudio.categoria_laboratorio === categoria.codigo),
  })).filter((categoria) => categoria.estudios.length > 0)
  const codigosConocidos = new Set(categoriasLaboratorio.map((categoria) => categoria.codigo))
  const otros = estudios.filter((estudio) => !codigosConocidos.has(estudio.categoria_laboratorio))
  if (otros.length > 0) categorias.push({ codigo: null, nombre: 'Otros estudios', estudios: otros })
  return categorias
}

export function estadoSolicitud(estudios) {
  if (estudios.every((estudio) => estudio.estado === 'publicado')) return 'Publicado'
  if (estudios.every((estudio) => estudio.estado === 'pendiente_muestra')) return 'Pendiente de muestra'
  if (estudios.some((estudio) => estudio.estado === 'publicado')) return 'Parcialmente publicado'
  return 'En preparación'
}
