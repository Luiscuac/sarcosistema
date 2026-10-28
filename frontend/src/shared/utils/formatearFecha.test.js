import test from 'node:test'
import assert from 'node:assert/strict'
import { formatearFecha } from './formatearFecha.js'

test('la fecha se muestra en formato local boliviano', () => {
  assert.equal(formatearFecha('2026-10-22T10:00:00.000Z'), '22/10/2026')
  assert.equal(formatearFecha('1990-01-05'), '05/01/1990')
})

test('una fecha inválida no produce una fecha inventada', () => {
  assert.equal(formatearFecha('no-es-una-fecha'), 'Invalid Date')
})

test('la hora no se incluye en la salida', () => {
  assert.ok(!formatearFecha('2026-10-22T23:59:00.000Z').includes(':'))
})
