import test from 'node:test'
import assert from 'node:assert/strict'
import { accionPrincipalEco, contarImagenes, agregarArchivos, iniciarDatos, motivoBloqueoEco, pendientes, edadEnEstudio, resumenRegistro } from './informe.js'

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
test('el resumen del registro cuenta estructuras, fecha, conclusión y zona cuando corresponde', () => {
  const d = { tipo: 'ECO_RENAL', fecha_estudio: '2026-11-14', conclusion: '', zona: '', evaluaciones: { 'Riñón derecho': 'Ficticio.', 'Riñón izquierdo': '' } }
  const r = resumenRegistro(d, ['Riñón derecho', 'Riñón izquierdo'])
  assert.equal(r.total, 5)
  assert.equal(r.completos, 2)
  assert.deepEqual(r.faltan, ['Riñón izquierdo', 'Conclusión', 'Al menos una imagen'])
  assert.deepEqual(resumenRegistro(d, ['Riñón derecho', 'Riñón izquierdo'], 1).faltan, ['Riñón izquierdo', 'Conclusión'])
  assert.equal(resumenRegistro({ ...d, tipo: 'ECO_DOPPLER' }, ['Riñón derecho', 'Riñón izquierdo']).total, 6)
})
test('publicar se bloquea con faltantes, cambios sin guardar o sin borrador', () => {
  assert.match(motivoBloqueoEco({ faltan: ['Conclusión'], cambio: false, guardado: true }), /Conclusión/)
  assert.match(motivoBloqueoEco({ faltan: [], cambio: true, guardado: true }), /Guarda el borrador antes/)
  assert.match(motivoBloqueoEco({ faltan: [], cambio: false, guardado: false }), /Guarda el borrador para/)
  assert.equal(motivoBloqueoEco({ faltan: [], cambio: false, guardado: true }), null)
})
test('la acción principal sigue el estado del estudio', () => {
  assert.deepEqual(accionPrincipalEco({ estudio_id: 7, estado: 'pendiente_muestra', informe: null }), { etiqueta: 'Registrar hallazgos', ruta: '/ecografia/estudios/7/registro' })
  assert.equal(accionPrincipalEco({ estudio_id: 7, estado: 'resultado_en_preparacion', informe: {} }).etiqueta, 'Continuar registro')
  assert.equal(accionPrincipalEco({ estudio_id: 7, estado: 'publicado', informe: {} }).ruta, '/ecografia/estudios/7/informe')
})
test('solo las imágenes (no los PDF) cuentan para publicar', () => {
  assert.equal(contarImagenes([{ mime_type: 'application/pdf' }], []), 0)
  assert.equal(contarImagenes([{ mime_type: 'image/png' }, { mime_type: 'application/dicom' }], []), 2)
  assert.equal(contarImagenes([], [{ name: 'corte.dcm', type: '' }, { name: 'a.pdf', type: 'application/pdf' }]), 1)
})
