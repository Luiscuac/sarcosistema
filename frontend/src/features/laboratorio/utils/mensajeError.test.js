import test from 'node:test'
import assert from 'node:assert/strict'
import { mensajeError } from './mensajeError.js'

test('usa el mensaje del servidor cuando es texto', () => {
  assert.equal(mensajeError({ response: { data: { detail: 'Faltan campos obligatorios: Hb' } } }), 'Faltan campos obligatorios: Hb')
})

test('une los mensajes de validación sin mostrar rutas internas', () => {
  const error = { response: { data: { detail: [{ loc: ['body', 'x'], msg: 'Campo requerido' }, { msg: 'Valor inválido' }] } } }
  assert.equal(mensajeError(error), 'Campo requerido · Valor inválido')
})

test('distingue la falta de conexión y usa el mensaje predeterminado en otros casos', () => {
  assert.match(mensajeError({ code: 'ERR_NETWORK' }), /conexión/)
  assert.equal(mensajeError({ response: { status: 500, data: {} } }, 'No se pudo guardar.'), 'No se pudo guardar.')
})
