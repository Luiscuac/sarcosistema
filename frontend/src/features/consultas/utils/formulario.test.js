import test from 'node:test'
import assert from 'node:assert/strict'
import {
  calcularImc, conPresion, confirmarSalida, formularioAPayload, formularioInicial,
  sincronizarPresion, transferirEnfermeria,
} from './formulario.js'

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

test('acepta coma decimal y no envía el texto visible de la presión', () => {
  const form = conPresion({ ...formularioInicial(), motivo_consulta: 'Fiebre', diagnostico_principal: 'X', temperatura_c: '38,4' }, '130/85')
  const payload = formularioAPayload(form, 3, 'clave')
  assert.equal(payload.temperatura_c, 38.4)
  assert.equal(payload.presion_sistolica, 130)
  assert.equal(payload.presion_diastolica, 85)
  assert.equal(payload.presion, undefined)
})

test('una presión mal escrita deja vacías sistólica y diastólica', () => {
  const form = conPresion(formularioInicial(), '80/130')
  assert.equal(form.presion, '80/130')
  assert.equal(form.presion_sistolica, '')
  assert.equal(sincronizarPresion({ presion_sistolica: '120', presion_diastolica: '70' }).presion, '120/70')
})

test('los datos de enfermería solo llenan campos vacíos y no pisan lo escrito por el médico', () => {
  const registro = { temperatura_c: 38.2, presion_sistolica: 120, presion_diastolica: 80, motivo_consulta: 'Tos', sintomas: null, dolor_escala: 6 }
  const inicial = { ...formularioInicial(), motivo_consulta: 'Tos seca hace 3 días' }
  const { form, copiados, conservados } = transferirEnfermeria(inicial, registro)
  assert.equal(form.temperatura_c, '38.2')
  assert.equal(form.presion, '120/80')
  assert.equal(form.motivo_consulta, 'Tos seca hace 3 días')
  assert.deepEqual(copiados, ['temperatura_c', 'presion_sistolica', 'presion_diastolica'])
  assert.deepEqual(conservados, ['motivo_consulta'])
  assert.equal('dolor_escala' in form, false)
})
