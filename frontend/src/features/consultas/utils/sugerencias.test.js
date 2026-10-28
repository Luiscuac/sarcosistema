import test from 'node:test'
import assert from 'node:assert/strict'
import { aplicarSugerencia, deshacerSugerencia } from './sugerencias.js'

test('aceptar modifica solo un campo vacío y conserva los demás', () => {
  const resultado = aplicarSugerencia({ motivo_consulta: '', diagnostico_principal: 'Manual' },
    { campo: 'motivo_consulta', valor: 'Dolor', ambiguo: false })
  assert.equal(resultado.aplicada, true)
  assert.deepEqual(resultado.form, { motivo_consulta: 'Dolor', diagnostico_principal: 'Manual' })
})

test('campo manual nunca se sobrescribe sin confirmación explícita', () => {
  const actual = { diagnostico_principal: 'Manual' }
  const item = { campo: 'diagnostico_principal', valor: 'Sospecha de gastritis' }
  const resultado = aplicarSugerencia(actual, item)
  assert.equal(resultado.requiereConfirmacion, true)
  assert.deepEqual(resultado.form, actual)
  const aceptada = aplicarSugerencia(actual, item, true)
  assert.equal(aceptada.form.diagnostico_principal, 'Sospecha de gastritis')
})

test('deshacer no borra una corrección manual posterior', () => {
  const aplicacion = { campo: 'sintomas', valor: 'Tos', anterior: '' }
  assert.deepEqual(deshacerSugerencia({ sintomas: 'Tos' }, aplicacion), { sintomas: '' })
  assert.deepEqual(deshacerSugerencia({ sintomas: 'Tos corregida' }, aplicacion), { sintomas: 'Tos corregida' })
})

test('deshacer no sobrescribe al médico que cambió y volvió al mismo texto', () => {
  const item = { campo: 'sintomas', valor: 'Tos', anterior: 'Manual', revisionAplicacion: 1 }
  assert.deepEqual(deshacerSugerencia({ sintomas: 'Tos' }, item, 3), { sintomas: 'Tos' })
  assert.deepEqual(deshacerSugerencia({ sintomas: 'Tos' }, item, 1), { sintomas: 'Manual' })
})

test('no aplicar campo ambiguo ni identidad de paciente del proveedor', () => {
  const form = { sintomas: '' }
  assert.equal(aplicarSugerencia(form, { campo: 'sintomas', valor: '¿Fiebre?', ambiguo: true }).aplicada, false)
  assert.equal(aplicarSugerencia(form, { campo: 'paciente_id', valor: '999' }).aplicada, false)
})
