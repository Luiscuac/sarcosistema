import test from 'node:test'
import assert from 'node:assert/strict'
import { mensajeDeError, formatearTiempo } from './audio.js'

test('los errores de permiso y de dispositivo tienen mensaje propio', () => {
  assert.match(mensajeDeError({ name: 'NotAllowedError' }), /micrófono\. Permite/)
  assert.match(mensajeDeError({ name: 'DevicesNotFoundError' }), /No se encontró un micrófono/)
})

test('cada estado HTTP del backend tiene su mensaje explícito', () => {
  assert.match(mensajeDeError({ response: { status: 413 } }), /límite de 20 MB/)
  assert.match(mensajeDeError({ response: { status: 415 } }), /formato de audio/)
  assert.match(mensajeDeError({ response: { status: 503 } }), /modelo local no está disponible/)
})

test('sin respuesta del servidor se distingue del fallo del modelo', () => {
  assert.match(mensajeDeError({ name: 'TypeError' }), /Comprueba que el backend esté iniciado/i)
  assert.match(mensajeDeError({ name: 'NotSupportedError' }), /navegador no permite grabar/i)
})

test('un fallo del servidor distinto no filtra detalles técnicos', () => {
  const mensaje = mensajeDeError({ response: { status: 500, data: { detail: 'traceback interno' } } })
  assert.ok(!mensaje.includes('traceback interno'))
  assert.match(mensaje, /No se pudo transcribir la grabación/)
})

test('el cronómetro siempre muestra mm:ss', () => {
  assert.equal(formatearTiempo(0), '00:00')
  assert.equal(formatearTiempo(61), '01:01')
  assert.equal(formatearTiempo(600), '10:00')
})
