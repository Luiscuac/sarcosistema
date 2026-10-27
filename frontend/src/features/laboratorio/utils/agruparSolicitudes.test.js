import test from 'node:test'
import assert from 'node:assert/strict'
import { agruparSolicitudes, agruparPorCategoria, estadoSolicitud } from './agruparSolicitudes.js'

test('una solicitud con varias pruebas ocupa un grupo, aun con varios departamentos', () => {
  const estudios = [
    { solicitud_id: 10, referencia_solicitud: 'SOL-10', paciente_id: 1, paciente_nombre: 'Paciente ficticio', categoria_laboratorio: 'hematologia', estado: 'pendiente_muestra' },
    { solicitud_id: 10, referencia_solicitud: 'SOL-10', paciente_id: 1, paciente_nombre: 'Paciente ficticio', categoria_laboratorio: 'bioquimica', estado: 'resultado_en_preparacion' },
    { solicitud_id: 11, referencia_solicitud: 'SOL-11', paciente_id: 1, paciente_nombre: 'Paciente ficticio', categoria_laboratorio: 'serologia', estado: 'pendiente_muestra' },
  ]

  const solicitudes = agruparSolicitudes(estudios)
  assert.equal(solicitudes.length, 2)
  assert.equal(solicitudes[0].estudios.length, 2)
  assert.deepEqual(agruparPorCategoria(solicitudes[0].estudios).map((grupo) => grupo.nombre), ['Hematología', 'Bioquímica'])
  assert.equal(estadoSolicitud(solicitudes[0].estudios), 'En preparación')
})

test('la publicación parcial conserva las pruebas restantes en la solicitud', () => {
  assert.equal(estadoSolicitud([{ estado: 'publicado' }, { estado: 'pendiente_muestra' }]), 'Parcialmente publicado')
})

test('los estudios sin categoría conocida siguen visibles', () => {
  const grupos = agruparPorCategoria([{ categoria_laboratorio: 'nueva_categoria' }, { categoria_laboratorio: null }])
  assert.equal(grupos.length, 1)
  assert.equal(grupos[0].nombre, 'Otros estudios')
  assert.equal(grupos[0].estudios.length, 2)
})
