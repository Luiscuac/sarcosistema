import test from 'node:test'
import assert from 'node:assert/strict'
import { calcularImc, formularioAPayload, confirmarSalida } from './formulario.js'

test('IMC es nulo si faltan mediciones y se calcula con kg y cm válidos', () => {
  assert.equal(calcularImc('', '170'), null)
  assert.equal(calcularImc('70', '0'), null)
  assert.equal(calcularImc('72', '180'), 22.2)
})

test('payload usa null para vacíos y nunca envía identidad profesional ni fecha', () => {
  const payload = formularioAPayload({ motivo_consulta: '  Dolor ', diagnostico_principal: ' Manual ',
    peso_kg: '', sintomas: '', medico_id: 4, fecha_hora_inicio: 'mañana' }, 8, '11111111-1111-4111-8111-111111111111')
  assert.equal(payload.paciente_id, 8)
  assert.equal(payload.peso_kg, null)
  assert.equal(payload.sintomas, null)
  assert.equal(payload.motivo_consulta, 'Dolor')
  assert.equal(payload.medico_id, undefined)
  assert.equal(payload.fecha_hora_inicio, undefined)
})

test('descartar cambios requiere confirmación, sin cambios no interrumpe navegación', () => {
  assert.equal(confirmarSalida(false, () => { throw new Error('No solicitar confirmación') }), true)
  assert.equal(confirmarSalida(true, () => false), false)
  assert.equal(confirmarSalida(true, () => true), true)
})
