import test from 'node:test'
import assert from 'node:assert/strict'
import { accionPrincipalEco, contarImagenes, agregarArchivos, iniciarDatos, motivoBloqueoEco, pendientes, edadEnEstudio, resumenRegistro } from './informe.js'
import { aplicarPropuestaEcografia, deshacerPropuestaEcografia } from './asistente.js'

const archivo = name => ({ name, size: 15, lastModified: 1 })
test('la edad del informe corresponde a la fecha del estudio', () => {
  assert.equal(edadEnEstudio('2000-11-15', '2026-11-14'), '25 aÃ±os')
  assert.equal(edadEnEstudio(null, '2026-11-14'), 'No registrada')
})
test('acumula imÃ¡genes en varias selecciones sin duplicar archivos idÃ©nticos', () => {
  const a = archivo('a.png'), b = archivo('b.png')
  assert.deepEqual(agregarArchivos([a], [a, b], 10), [a, b])
})
test('el mÃ¡ximo incluye los adjuntos ya guardados y no altera la selecciÃ³n al fallar', () => {
  const originales = [archivo('a.png')]
  assert.throws(() => agregarArchivos(originales, [archivo('b.png')], 2, 1), /hasta 2/)
  assert.equal(originales.length, 1)
})
test('un informe antiguo conserva su texto sin inventar hallazgos de Ã³rganos', () => {
  const d = iniciarDatos({ tipo_estudio_codigo: 'ECO_RENAL', organos: ['RiÃ±Ã³n derecho'], informe: { descripcion_texto: 'Texto histÃ³rico ficticio.' } })
  assert.equal(d.observaciones, 'Texto histÃ³rico ficticio.')
  assert.equal(d.evaluaciones['RiÃ±Ã³n derecho'], '')
  assert.equal(d.conclusion, '')
})
test('no se permite publicar sin observaciones, conclusiÃ³n y zona de Doppler', () => {
  const d = { tipo: 'ECO_DOPPLER', fecha_estudio: '2026-11-14', conclusion: '', zona: '', evaluaciones: { Arterias: '' } }
  assert.deepEqual(pendientes(d, ['Arterias']), ['Arterias', 'ConclusiÃ³n', 'Zona estudiada'])
  assert.deepEqual(pendientes({ ...d, zona: 'Zona FICTICIA', conclusion: 'ConclusiÃ³n ficticia.', evaluaciones: { Arterias: 'No evaluadas en esta simulaciÃ³n.' } }, ['Arterias']), [])
})
test('aplica la propuesta de un Ã³rgano sin perder texto manual y permite deshacerla', () => {
  const original = { tipo: 'ECO_RENAL', evaluaciones: { 'RiÃ±Ã³n derecho': 'Texto manual ficticio.' } }
  const resultado = aplicarPropuestaEcografia(original, {
    campo: 'evaluaciones', organo: 'RiÃ±Ã³n derecho', valor: 'Cita dictada ficticia.',
  })
  assert.equal(resultado.datos.evaluaciones['RiÃ±Ã³n derecho'], 'Texto manual ficticio.\nCita dictada ficticia.')
  assert.deepEqual(deshacerPropuestaEcografia(resultado.datos,
    { organo: 'RiÃ±Ã³n derecho' }, resultado.anterior), original)
})
test('no deshace una propuesta si el profesional editÃ³ el campo despuÃ©s de aceptarla', () => {
  const item = { organo: 'RiÃ±Ã³n derecho', valor: 'Cita dictada ficticia.' }
  const datos = { evaluaciones: { 'RiÃ±Ã³n derecho': 'Texto manual.\nCita editada despuÃ©s.' } }
  assert.equal(deshacerPropuestaEcografia(datos, item, 'Texto manual.'), null)
})
test('el resumen del registro cuenta estructuras, fecha, conclusiÃ³n y zona cuando corresponde', () => {
  const d = { tipo: 'ECO_RENAL', fecha_estudio: '2026-11-14', conclusion: '', zona: '', evaluaciones: { 'RiÃ±Ã³n derecho': 'Ficticio.', 'RiÃ±Ã³n izquierdo': '' } }
  const r = resumenRegistro(d, ['RiÃ±Ã³n derecho', 'RiÃ±Ã³n izquierdo'])
  assert.equal(r.total, 5)
  assert.equal(r.completos, 2)
  assert.deepEqual(r.faltan, ['RiÃ±Ã³n izquierdo', 'ConclusiÃ³n', 'Al menos una imagen'])
  assert.deepEqual(resumenRegistro(d, ['RiÃ±Ã³n derecho', 'RiÃ±Ã³n izquierdo'], 1).faltan, ['RiÃ±Ã³n izquierdo', 'ConclusiÃ³n'])
  assert.equal(resumenRegistro({ ...d, tipo: 'ECO_DOPPLER' }, ['RiÃ±Ã³n derecho', 'RiÃ±Ã³n izquierdo']).total, 6)
})
test('publicar se bloquea con faltantes, cambios sin guardar o sin borrador', () => {
  assert.match(motivoBloqueoEco({ faltan: ['ConclusiÃ³n'], cambio: false, guardado: true }), /ConclusiÃ³n/)
  assert.match(motivoBloqueoEco({ faltan: [], cambio: true, guardado: true }), /Guarda el borrador antes/)
  assert.match(motivoBloqueoEco({ faltan: [], cambio: false, guardado: false }), /Guarda el borrador para/)
  assert.equal(motivoBloqueoEco({ faltan: [], cambio: false, guardado: true }), null)
})
test('la acciÃ³n principal sigue el estado del estudio', () => {
  assert.deepEqual(accionPrincipalEco({ estudio_id: 7, estado: 'pendiente_muestra', informe: null }), { etiqueta: 'Registrar hallazgos', ruta: '/ecografia/estudios/7/registro' })
  assert.equal(accionPrincipalEco({ estudio_id: 7, estado: 'resultado_en_preparacion', informe: {} }).etiqueta, 'Continuar registro')
  assert.equal(accionPrincipalEco({ estudio_id: 7, estado: 'publicado', informe: {} }).ruta, '/ecografia/estudios/7/informe')
})
test('solo las imÃ¡genes (no los PDF) cuentan para publicar', () => {
  assert.equal(contarImagenes([{ mime_type: 'application/pdf' }], []), 0)
  assert.equal(contarImagenes([{ mime_type: 'image/png' }, { mime_type: 'application/dicom' }], []), 2)
  assert.equal(contarImagenes([], [{ name: 'corte.dcm', type: '' }, { name: 'a.pdf', type: 'application/pdf' }]), 1)
})
