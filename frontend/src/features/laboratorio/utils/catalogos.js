// Etiquetas visibles del laboratorio: una sola fuente para todas las pantallas.

export const AREAS_LABORATORIO = [
  { codigo: 'hematologia', nombre: 'Hematología' },
  { codigo: 'bioquimica', nombre: 'Bioquímica' },
  { codigo: 'serologia', nombre: 'Serología' },
  { codigo: 'copro_orina', nombre: 'Copro y orina' },
]

const NOMBRES_AREA = Object.fromEntries(AREAS_LABORATORIO.map(({ codigo, nombre }) => [codigo, nombre]))

export function nombreArea(codigo) {
  return NOMBRES_AREA[codigo] ?? codigo ?? 'Laboratorio'
}

export const ETIQUETAS_ESTADO_ESTUDIO = {
  pendiente_muestra: 'Pendiente de muestra',
  resultado_en_preparacion: 'En preparación',
  publicado: 'Publicado',
  no_realizado: 'No realizado',
}

export const ESTADOS_FINALES = new Set(['publicado', 'no_realizado'])

export const MOTIVOS_INCIDENCIA = [
  { codigo: 'muestra_no_entregada', nombre: 'Muestra no entregada' },
  { codigo: 'toma_rechazada', nombre: 'Toma rechazada' },
  { codigo: 'toma_no_realizada', nombre: 'Toma no realizada' },
]

export function nombreMotivoIncidencia(codigo) {
  return MOTIVOS_INCIDENCIA.find((motivo) => motivo.codigo === codigo)?.nombre ?? codigo
}

export const SEXOS = [
  { codigo: 'F', nombre: 'Femenino' },
  { codigo: 'M', nombre: 'Masculino' },
  { codigo: 'otro', nombre: 'Otro' },
  { codigo: 'no_especificado', nombre: 'No especificado' },
]

export function nombreSexo(codigo) {
  return SEXOS.find((sexo) => sexo.codigo === codigo)?.nombre ?? 'No registrado'
}

export const TIPOS_DOCUMENTO = ['CI', 'Pasaporte', 'Carnet de extranjero']
