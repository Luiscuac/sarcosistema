import test from 'node:test'
import assert from 'node:assert/strict'
import { esDeHoy, fecha, fechaLocalDe } from './paciente.js'

const local = (anio, mes, dia, hora = 12, minuto = 0) => new Date(anio, mes - 1, dia, hora, minuto)

test('una fecha de calendario se muestra tal cual, sin restar un día', () => {
  assert.equal(fecha('2026-11-10'), local(2026, 11, 10).toLocaleDateString('es-BO', { day: '2-digit', month: '2-digit', year: 'numeric' }))
  assert.equal(fecha(''), 'No registrada')
})

test('un instante con hora se muestra en el día local, no en el día UTC', () => {
  const nocheLocal = local(2026, 11, 10, 22, 30) // en UTC-4 ya es 11/11 en UTC
  assert.equal(fecha(nocheLocal.toISOString()), fecha('2026-11-10'))
})

test('la fecha local de un instante no pasa por UTC', () => {
  assert.equal(fechaLocalDe(local(2026, 1, 5, 23, 59)), '2026-01-05')
  assert.equal(fechaLocalDe(local(2026, 12, 31, 0, 1)), '2026-12-31')
})

test('reconoce lo publicado hoy', () => {
  const hoy = local(2026, 11, 10, 15)
  assert.equal(esDeHoy(local(2026, 11, 10, 8).toISOString(), hoy), true)
  assert.equal(esDeHoy(local(2026, 11, 9, 23).toISOString(), hoy), false)
  assert.equal(esDeHoy(null, hoy), false)
})
