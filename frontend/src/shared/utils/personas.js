/** Datos de personas comunes a todos los módulos (pacientes). */

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
