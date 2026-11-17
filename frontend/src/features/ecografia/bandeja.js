export const VISTAS = [
  { codigo: 'pendiente_muestra', nombre: 'Pendientes', accion: 'Realizar estudio' },
  { codigo: 'resultado_en_preparacion', nombre: 'En preparación', accion: 'Continuar informe' },
  { codigo: 'publicado', nombre: 'Publicados', accion: 'Ver informe' },
]

const normalizar = valor => String(valor || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLocaleLowerCase('es')

export function filtrarEstudios(estudios, { estado = 'todos', buscar = '', tipo = 'todos' } = {}) {
  const termino = normalizar(buscar.trim())
  return estudios.filter(e => (estado === 'todos' || e.estado === estado)
    && (tipo === 'todos' || e.tipo_estudio_nombre === tipo)
    && normalizar(`${e.paciente_nombre} ${e.referencia_estudio} ${e.referencia_solicitud} ${e.tipo_estudio_nombre}`).includes(termino))
    .sort((a, b) => Number(b.prioridad === 'urgente' && b.estado !== 'publicado') - Number(a.prioridad === 'urgente' && a.estado !== 'publicado'))
}
