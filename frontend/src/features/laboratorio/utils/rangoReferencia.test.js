import test from 'node:test'
import assert from 'node:assert/strict'
import { evaluarValor, interpretarNumero, interpretarRango } from './rangoReferencia.js'

test('distingue comas de miles, coma decimal y punto decimal', () => {
  assert.equal(interpretarNumero('3,500,000'), 3500000)
  assert.equal(interpretarNumero('0,5'), 0.5)
  assert.equal(interpretarNumero('1.010'), 1.01)
  assert.equal(interpretarNumero('abc'), null)
})

test('interpreta los formatos transcritos del catálogo', () => {
  assert.deepEqual(interpretarRango('3,500,000 a 5,500,000/mm³'), { min: 3500000, max: 5500000 })
  assert.deepEqual(interpretarRango('11.0 a 16.0 g/dL'), { min: 11, max: 16 })
  assert.deepEqual(interpretarRango('Hasta 200 mg/dL'), { min: null, max: 200 })
  assert.deepEqual(interpretarRango('Menor a 190 mg/dL'), { min: null, max: 190 })
  assert.deepEqual(interpretarRango('Mayor a 45 mg/dL'), { min: 45, max: null })
})

test('no inventa un rango a partir de texto cualitativo o incoherente', () => {
  assert.equal(interpretarRango('Negativo'), null)
  assert.equal(interpretarRango(''), null)
  assert.equal(interpretarRango('10 a 2'), null)
})

test('marca bajo o alto solo para valores numéricos con rango interpretable', () => {
  assert.equal(evaluarValor('9.5', '11.0 a 16.0 g/dL', 'decimal'), 'bajo')
  assert.equal(evaluarValor('17', '11.0 a 16.0 g/dL', 'decimal'), 'alto')
  assert.equal(evaluarValor('12,5', '11.0 a 16.0 g/dL', 'decimal'), null)
  assert.equal(evaluarValor('250', 'Hasta 200 mg/dL', 'entero'), 'alto')
  assert.equal(evaluarValor('', '11.0 a 16.0 g/dL', 'decimal'), null)
  assert.equal(evaluarValor('Positivo', 'Negativo', 'cualitativo'), null)
  assert.equal(evaluarValor('300', 'Hasta 200 mg/dL', 'texto'), null)
})

test('un valor único con su unidad es el valor esperado', () => {
  assert.deepEqual(interpretarRango('0 mg/dL'), { min: 0, max: 0 })
  assert.deepEqual(interpretarRango('0 PCM'), { min: 0, max: 0 })
  assert.equal(evaluarValor('0', '0 mg/dL', 'decimal'), null)
  assert.equal(evaluarValor('50', '0 mg/dL', 'decimal'), 'alto')
  assert.equal(evaluarValor('2', '0 PCM', 'entero'), 'alto')
  // No confunde rangos ni textos con un valor único.
  assert.deepEqual(interpretarRango('70–115 mg/dL'), { min: 70, max: 115 })
  assert.equal(interpretarRango('Normal o 0 mg/dL'), null)
  assert.equal(interpretarRango('Negativo'), null)
})

test('los límites del rango cuentan como dentro del rango', () => {
  assert.equal(evaluarValor('11', '11.0 a 16.0 g/dL', 'decimal'), null)
  assert.equal(evaluarValor('16.0', '11.0 a 16.0 g/dL', 'decimal'), null)
  assert.equal(evaluarValor('10.9', '11.0 a 16.0 g/dL', 'decimal'), 'bajo')
  assert.equal(evaluarValor('16.1', '11.0 a 16.0 g/dL', 'decimal'), 'alto')
  assert.equal(evaluarValor('200', 'Hasta 200 mg/dL', 'entero'), null)
})
