import test from 'node:test'
import assert from 'node:assert/strict'
import { accionPrincipalRx, pasoActualRx, resumenAdquisicion, resumenInforme } from './flujo.js'

test('adquisición: falta lo mismo que exige el servidor', () => {
  const vacio = resumenAdquisicion({ proyecciones_realizadas: [] }, { requiere_lateralidad: true }, 0)
  assert.equal(vacio.total, 4)
  assert.equal(vacio.completos, 0)
  const listo = resumenAdquisicion({ proyecciones_realizadas: ['PA'], lateralidad_realizada: 'derecha', fecha_hora_adquisicion: '2026-11-23T10:00' }, { requiere_lateralidad: true }, 1)
  assert.deepEqual(listo.faltan, [])
  assert.equal(resumenAdquisicion({ proyecciones_realizadas: ['PA'], fecha_hora_adquisicion: 'x' }, {}, 0).faltan.length, 1)
})

test('informe: conclusión, al menos un hallazgo e imágenes (o informe externo)', () => {
  assert.equal(resumenInforme({ generales: {}, apartados: {} }, null, 0).faltan.length, 3)
  assert.deepEqual(resumenInforme({ generales: { conclusion: 'Ficticia.' }, apartados: { campos: 'Ficticio.' } }, null, 1).faltan, [])
  assert.deepEqual(resumenInforme({ generales: { conclusion: 'Ficticia.' }, apartados: {} }, 'Texto final ficticio.', 0, true).faltan, [])
})

test('paso actual del recorrido según la etapa', () => {
  assert.equal(pasoActualRx('pendiente_realizacion'), 1)
  assert.equal(pasoActualRx('borrador'), 2)
  assert.equal(pasoActualRx('entregado'), 4)
})

test('acción principal según etapa y permisos', () => {
  const d = (etapa, permisos) => ({ estudio: { estudio_id: 9, etapa }, permisos })
  assert.deepEqual(accionPrincipalRx(d('pendiente_realizacion', { registrar_adquisicion: true })), { etiqueta: 'Registrar adquisición', ruta: '/rayos-x/gestion/estudios/9/adquisicion' })
  assert.equal(accionPrincipalRx(d('borrador', { redactar_informe: true })).ruta, '/rayos-x/gestion/estudios/9/informe')
  assert.equal(accionPrincipalRx(d('validado', { entregar: true })).accion, 'entregar')
  assert.equal(accionPrincipalRx(d('entregado', {})).ruta, '/rayos-x/gestion/estudios/9/impresion')
  assert.equal(accionPrincipalRx(d('pendiente_informe', {})), null)
})
