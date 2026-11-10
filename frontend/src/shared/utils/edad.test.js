import test from 'node:test'
import assert from 'node:assert/strict'
import { calcularEdad, describirEdad } from './edad.js'

test('cuenta los años cumplidos según el día del cumpleaños', () => {
  const hoy = new Date(2026, 10, 9)
  assert.equal(calcularEdad('1990-11-09', hoy), 36)
  assert.equal(calcularEdad('1990-11-10', hoy), 35)
  assert.equal(calcularEdad('2025-05-01', hoy), 1)
})

test('no muestra edad con fechas ausentes, inválidas o futuras', () => {
  const hoy = new Date(2026, 10, 9)
  assert.equal(calcularEdad(null, hoy), null)
  assert.equal(calcularEdad('09/11/1990', hoy), null)
  assert.equal(calcularEdad('2027-01-01', hoy), null)
  assert.equal(describirEdad('2027-01-01', hoy), '')
})

test('usa singular y plural', () => {
  const hoy = new Date(2026, 10, 9)
  assert.equal(describirEdad('2025-11-01', hoy), '1 año')
  assert.equal(describirEdad('2000-01-01', hoy), '26 años')
})
