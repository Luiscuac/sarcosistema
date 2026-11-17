import test from 'node:test'
import assert from 'node:assert/strict'
import { filtrarEstudios } from './bandeja.js'

const estudios = [
  { estudio_id: 1, estado: 'pendiente_muestra', paciente_nombre: 'Paciente Álvarez', tipo_estudio_nombre: 'Ecografía renal', referencia_solicitud: 'IMG-001' },
  { estudio_id: 2, estado: 'pendiente_muestra', paciente_nombre: 'Paciente Ficticio', tipo_estudio_nombre: 'Ecografía abdominal', prioridad: 'urgente' },
  { estudio_id: 3, estado: 'publicado', paciente_nombre: 'Paciente Ficticio', tipo_estudio_nombre: 'Ecografía renal', prioridad: 'urgente' },
]
test('combina estado, tipo y búsqueda sin depender de tildes', () => {
  assert.deepEqual(filtrarEstudios(estudios, { estado: 'pendiente_muestra', tipo: 'Ecografía renal', buscar: 'alvarez' }).map(e => e.estudio_id), [1])
  assert.deepEqual(filtrarEstudios(estudios, { buscar: 'img-001' }).map(e => e.estudio_id), [1])
})
test('prioriza urgentes pendientes sin mover publicados por prioridad ni alterar la lista original', () => {
  assert.deepEqual(filtrarEstudios(estudios).map(e => e.estudio_id), [2, 1, 3])
  assert.deepEqual(estudios.map(e => e.estudio_id), [1, 2, 3])
})
