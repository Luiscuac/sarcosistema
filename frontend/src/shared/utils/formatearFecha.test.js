import test from 'node:test'
import assert from 'node:assert/strict'
import process from 'node:process'
import { fechaHoy, formatearFecha, formatearFechaHora } from './formatearFecha.js'

// Hora de Bolivia (UTC-4), fija para que las pruebas no dependan de la PC.
process.env.TZ = 'America/La_Paz'

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

test('un instante con hora se muestra con el día local, no con el día UTC', () => {
  // 01:00 UTC del 24 = 21:00 del 23 en Bolivia
  assert.equal(formatearFecha('2026-11-24T01:00:00Z'), '23/11/2026')
})

test('fecha y hora en formato dd/mm/aaaa hh:mm sin segundos', () => {
  assert.equal(formatearFechaHora('2026-11-24T01:05:30Z'), '23/11/2026 21:05')
  assert.equal(formatearFechaHora(null), '—')
  assert.equal(formatearFechaHora('basura', 'Sin fecha'), 'Sin fecha')
})

test('hoy en formato de campo de fecha, con la fecha local', () => {
  assert.equal(fechaHoy(new Date(2026, 0, 5, 23, 30)), '2026-01-05')
})
