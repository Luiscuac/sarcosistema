import test from 'node:test'
import assert from 'node:assert/strict'
import {
  FORMULARIO_VACIO, avisoDeCampo, calcularImc, cuerpoDesdeFormulario, errorDeCampo,
  erroresDelFormulario, formularioDesdeRegistro, formularioVacio, leerNumero, leerPresion,
  resumenDelFormulario,
} from './signosVitales.js'

test('lee números con coma o punto decimal', () => {
  assert.equal(leerNumero('36,5'), 36.5)
  assert.equal(leerNumero(' 36.5 '), 36.5)
  assert.equal(leerNumero(''), null)
  assert.ok(Number.isNaN(leerNumero('36,5,1')))
  assert.ok(Number.isNaN(leerNumero('-3')))
})

test('lee la presión en un solo campo y aplica las reglas del backend', () => {
  assert.deepEqual(leerPresion('120/80'), { sistolica: 120, diastolica: 80 })
  assert.deepEqual(leerPresion(' 120 / 80 '), { sistolica: 120, diastolica: 80 })
  assert.equal(leerPresion(''), null)
  assert.ok(leerPresion('120').error)
  assert.ok(leerPresion('80/120').error)
  assert.ok(leerPresion('350/80').error)
})

test('valida los mismos límites que AdmisionRequest', () => {
  assert.equal(errorDeCampo('temperatura_c', '36,8'), null)
  assert.match(errorDeCampo('temperatura_c', '24'), /al menos 25/)
  assert.match(errorDeCampo('temperatura_c', '46'), /superar 45/)
  assert.match(errorDeCampo('peso_kg', '0'), /mayor que 0/)
  assert.match(errorDeCampo('saturacion_oxigeno', '101'), /superar 100/)
  assert.match(errorDeCampo('frecuencia_cardiaca', 'abc'), /solo números/)
  assert.equal(errorDeCampo('peso_kg', ''), null)
})

test('resalta valores fuera de lo habitual sin confundirlos con errores', () => {
  assert.deepEqual(avisoDeCampo('temperatura_c', '38,2'), { nivel: 'alto', texto: 'Fiebre' })
  assert.equal(avisoDeCampo('temperatura_c', '37,9'), null)
  assert.deepEqual(avisoDeCampo('saturacion_oxigeno', '90'), { nivel: 'bajo', texto: 'Saturación baja' })
  assert.deepEqual(avisoDeCampo('presion', '150/85'), { nivel: 'alto', texto: 'Presión elevada' })
  assert.deepEqual(avisoDeCampo('presion', '85/55'), { nivel: 'bajo', texto: 'Presión baja' })
  assert.equal(avisoDeCampo('presion', '120/80'), null)
  assert.deepEqual(avisoDeCampo('dolor_escala', '8'), { nivel: 'alto', texto: 'Dolor intenso' })
  assert.equal(avisoDeCampo('temperatura_c', '50'), null) // es un error, no un aviso
})

test('no aplica referencias de adulto a FC, FR ni presión de menores', () => {
  assert.ok(avisoDeCampo('frecuencia_cardiaca', '120', 30))
  assert.equal(avisoDeCampo('frecuencia_cardiaca', '120', 4), null)
  assert.equal(avisoDeCampo('presion', '85/55', 4), null)
  assert.ok(avisoDeCampo('temperatura_c', '38,5', 4)) // la fiebre sí se marca
})

test('calcula el IMC solo con peso y talla válidos', () => {
  assert.equal(calcularImc('70', '175'), 22.9)
  assert.equal(calcularImc('70,5', '160'), 27.5)
  assert.equal(calcularImc('70', ''), null)
  assert.equal(calcularImc('70', '0'), null)
})

test('convierte formulario y registro en ambos sentidos', () => {
  const form = { ...FORMULARIO_VACIO, temperatura_c: '36,6', presion: '118/76', dolor_escala: '3', sintomas: ' tos ' }
  const cuerpo = cuerpoDesdeFormulario(form)
  assert.equal(cuerpo.temperatura_c, 36.6)
  assert.equal(cuerpo.presion_sistolica, 118)
  assert.equal(cuerpo.presion_diastolica, 76)
  assert.equal(cuerpo.dolor_escala, 3)
  assert.equal(cuerpo.sintomas, 'tos')
  assert.equal(cuerpo.peso_kg, null)
  assert.equal('presion' in cuerpo, false)
  const deVuelta = formularioDesdeRegistro(cuerpo)
  assert.equal(deVuelta.presion, '118/76')
  assert.equal(deVuelta.temperatura_c, '36.6')
})

test('lista errores, detecta formularios vacíos y arma el resumen', () => {
  assert.equal(formularioVacio(FORMULARIO_VACIO), true)
  assert.deepEqual(erroresDelFormulario({ ...FORMULARIO_VACIO, presion: '80/120' }).map(([campo]) => campo), ['presion'])
  const resumen = resumenDelFormulario({ ...FORMULARIO_VACIO, peso_kg: '70', talla_cm: '175', presion: '120/80', dolor_escala: '0' })
  assert.deepEqual(resumen.map((linea) => linea.campo), ['peso_kg', 'talla_cm', 'imc', 'presion', 'dolor_escala'])
})
