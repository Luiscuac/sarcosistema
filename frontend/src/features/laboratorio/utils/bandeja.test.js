import test from 'node:test'
import assert from 'node:assert/strict'
import { esperaProlongada, filtrarSolicitudes, progresoSolicitud, siguienteAccion, tiempoTranscurrido } from './bandeja.js'

const AHORA = new Date('2026-11-09T15:00:00').getTime()
const HORA = 60 * 60 * 1000

function solicitud(estados, extra = {}) {
  return {
    id: 7, referencia: 'SOL-7', paciente_nombre: 'Paciente ficticio', prioridad: 'sin_prioridad',
    fecha_solicitud: new Date(AHORA - HORA).toISOString(),
    estudios: estados.map(([estado, categoria = 'hematologia'], indice) => ({
      estudio_id: indice + 1, estado, categoria_laboratorio: categoria,
      referencia_estudio: `EST-${indice}`, tipo_estudio_nombre: 'Hemograma',
    })),
    ...extra,
  }
}

test('cuenta como avance los estudios publicados y los no realizados', () => {
  assert.deepEqual(progresoSolicitud(solicitud([['publicado'], ['no_realizado'], ['pendiente_muestra']]).estudios),
    { total: 3, finalizados: 2, completa: false })
})

test('la siguiente acción prioriza la muestra, luego los resultados y por último el informe', () => {
  assert.equal(siguienteAccion(solicitud([['pendiente_muestra'], ['resultado_en_preparacion']])).ruta,
    '/laboratorio/solicitudes/7?accion=muestra')
  assert.equal(siguienteAccion(solicitud([['publicado'], ['resultado_en_preparacion', 'bioquimica']])).ruta,
    '/laboratorio/solicitudes/7/areas/bioquimica/resultados')
  assert.equal(siguienteAccion(solicitud([['publicado'], ['no_realizado']])).tipo, 'informe')
})

test('un estudio sin área conocida abre la solicitud en lugar de una ruta inexistente', () => {
  assert.equal(siguienteAccion(solicitud([['resultado_en_preparacion', null]])).ruta, '/laboratorio/solicitudes/7')
})

test('describe el tiempo de espera en lenguaje simple', () => {
  assert.equal(tiempoTranscurrido(new Date(AHORA - 30 * 1000), AHORA), 'hace un momento')
  assert.equal(tiempoTranscurrido(new Date(AHORA - 5 * 60 * 1000), AHORA), 'hace 5 min')
  assert.equal(tiempoTranscurrido(new Date(AHORA - 3 * HORA), AHORA), 'hace 3 h')
  assert.equal(tiempoTranscurrido(new Date(AHORA - 49 * HORA), AHORA), 'hace 2 días')
})

test('las urgentes se destacan antes que las programadas y nunca las finalizadas', () => {
  const hace3h = new Date(AHORA - 3 * HORA).toISOString()
  assert.equal(esperaProlongada(solicitud([['pendiente_muestra']], { prioridad: 'urgente', fecha_solicitud: hace3h }), AHORA), true)
  assert.equal(esperaProlongada(solicitud([['pendiente_muestra']], { fecha_solicitud: hace3h }), AHORA), false)
  assert.equal(esperaProlongada(solicitud([['publicado']], { prioridad: 'urgente', fecha_solicitud: hace3h }), AHORA), false)
})

test('filtra por indicador, periodo y texto a la vez', () => {
  const urgente = solicitud([['pendiente_muestra']], { id: 1, prioridad: 'urgente', paciente_nombre: 'Ana Ficticia' })
  const antigua = solicitud([['resultado_en_preparacion']], { id: 2, fecha_solicitud: new Date(AHORA - 10 * 24 * HORA).toISOString() })
  const lista = [urgente, antigua]
  assert.deepEqual(filtrarSolicitudes(lista, { indicador: 'urgentes', ahora: AHORA }).map((s) => s.id), [1])
  assert.deepEqual(filtrarSolicitudes(lista, { indicador: 'preparacion', ahora: AHORA }).map((s) => s.id), [2])
  assert.deepEqual(filtrarSolicitudes(lista, { periodo: 'semana', ahora: AHORA }).map((s) => s.id), [1])
  assert.deepEqual(filtrarSolicitudes(lista, { busqueda: 'ana', ahora: AHORA }).map((s) => s.id), [1])
})
