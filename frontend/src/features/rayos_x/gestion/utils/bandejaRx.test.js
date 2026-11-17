import test from 'node:test'
import assert from 'node:assert/strict'
import { agruparPorSolicitud, contarIndicadores, filtrarYOrdenarEstudios } from './bandejaRx.js'

const estudios = [
  { estudio_id: 1, solicitud_id: 10, referencia_solicitud: 'RX-10', paciente_nombre: 'Ana Perez', paciente_documento: '111', categoria: 'torax', etapa: 'pendiente_informe', prioridad: 'sin_prioridad', fecha_solicitud: '2026-11-10', triaje: { indice: 0.8 } },
  { estudio_id: 2, solicitud_id: 11, referencia_solicitud: 'RX-11', paciente_nombre: 'Bea', paciente_documento: '222', categoria: 'craneo', etapa: 'pendiente_realizacion', prioridad: 'urgente', fecha_solicitud: '2026-11-12', triaje: null },
  { estudio_id: 3, solicitud_id: 10, referencia_solicitud: 'RX-10', paciente_nombre: 'Ana Perez', paciente_documento: '111', categoria: 'torax', etapa: 'borrador', prioridad: 'sin_prioridad', fecha_solicitud: '2026-11-10', triaje: { indice: 0.2 } },
  { estudio_id: 4, solicitud_id: 12, referencia_solicitud: 'RX-12', paciente_nombre: 'Ciro', paciente_documento: '333', categoria: 'torax', etapa: 'pendiente_informe', prioridad: 'sin_prioridad', fecha_solicitud: '2026-11-01', triaje: null },
]

test('filtra texto sin depender de tildes y aplica categoría e indicador', () => {
  assert.deepEqual(filtrarYOrdenarEstudios(estudios, { busqueda: 'ana pérez', categoria: 'torax', indicador: 'pendiente_informe' }).map((e) => e.estudio_id), [1])
})

test('ordena urgentes, índice de triaje y antiguedad', () => {
  assert.deepEqual(filtrarYOrdenarEstudios(estudios).map((e) => e.estudio_id), [2, 1, 3, 4])
})

test('agrupa filas y cuenta indicadores por estudio', () => {
  const grupos = agruparPorSolicitud(estudios)
  assert.equal(grupos.length, 3)
  assert.equal(grupos[0].estudios.length, 2)
  assert.deepEqual(contarIndicadores(estudios), {
    pendiente_realizacion: 1, en_adquisicion: 0, pendiente_informe: 2, borrador: 1, urgentes: 1,
  })
})
