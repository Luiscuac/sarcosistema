import test from 'node:test'
import assert from 'node:assert/strict'
import { agregarArchivos, iniciarDatos, pendientes, edadEnEstudio } from './informe.js'

const archivo = name => ({ name, size: 15, lastModified: 1 })
test('la edad del informe corresponde a la fecha del estudio', () => {
  assert.equal(edadEnEstudio('2000-11-15', '2026-11-14'), '25 años')
  assert.equal(edadEnEstudio(null, '2026-11-14'), 'No registrada')
})
test('acumula imágenes en varias selecciones sin duplicar archivos idénticos', () => {
  const a = archivo('a.png'), b = archivo('b.png')
  assert.deepEqual(agregarArchivos([a], [a, b], 10), [a, b])
})
test('el máximo incluye los adjuntos ya guardados y no altera la selección al fallar', () => {
  const originales = [archivo('a.png')]
  assert.throws(() => agregarArchivos(originales, [archivo('b.png')], 2, 1), /hasta 2/)
  assert.equal(originales.length, 1)
})
test('un informe antiguo conserva su texto sin inventar hallazgos de órganos', () => {
  const d = iniciarDatos({ tipo_estudio_codigo: 'ECO_RENAL', organos: ['Riñón derecho'], informe: { descripcion_texto: 'Texto histórico ficticio.' } })
  assert.equal(d.observaciones, 'Texto histórico ficticio.')
  assert.equal(d.evaluaciones['Riñón derecho'], '')
  assert.equal(d.conclusion, '')
})
test('no se permite publicar sin observaciones, conclusión y zona de Doppler', () => {
  const d = { tipo: 'ECO_DOPPLER', fecha_estudio: '2026-11-14', conclusion: '', zona: '', evaluaciones: { Arterias: '' } }
  assert.deepEqual(pendientes(d, ['Arterias']), ['Arterias', 'Conclusión', 'Zona estudiada'])
  assert.deepEqual(pendientes({ ...d, zona: 'Zona FICTICIA', conclusion: 'Conclusión ficticia.', evaluaciones: { Arterias: 'No evaluadas en esta simulación.' } }, ['Arterias']), [])
})
