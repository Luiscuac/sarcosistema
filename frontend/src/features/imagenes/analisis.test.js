import test from 'node:test'
import assert from 'node:assert/strict'
import { enProceso, validarRevision, mensajeError, snapshotCompatible, revisionVigente } from './analisis.js'

test('solo estados activos mantienen el seguimiento', () => {
  assert.equal(enProceso('en_cola'), true)
  assert.equal(enProceso('procesando'), true)
  assert.equal(enProceso('error'), false)
  assert.equal(enProceso('completado'), false)
})

test('revisión exige motivo y corrección explícitos', () => {
  assert.equal(validarRevision('rechazada', '', ''), false)
  assert.equal(validarRevision('corregida', 'Motivo', ''), false)
  assert.equal(validarRevision('corregida', 'Motivo', 'Corrección'), true)
  assert.equal(validarRevision('aceptada_como_propuesta', '', ''), true)
  assert.equal(validarRevision('', '', ''), false)
})

test('errores distinguen recursos sin filtrar detalles técnicos', () => {
  assert.match(mensajeError({ response: { status: 409 } }), /recarga/i)
  assert.match(mensajeError({ response: { status: 503 } }), /habilitada/i)
  assert.equal(mensajeError({ response: { status: 500, data: { detail: 'secreto' } } }).includes('secreto'), false)
})

test('un análisis histórico no se muestra junto a otro informe o archivo', () => {
  const a = { informe_id: 1, archivo_id: 2, archivo_sha256: 'hash', informe_texto: 'Original' }
  const d = { informe_id: 1, archivo: { id: 2, hash_sha256: 'hash' }, informe_texto: 'Original' }
  assert.equal(snapshotCompatible(a, d), true)
  assert.equal(snapshotCompatible(a, { ...d, informe_id: 9 }), false)
  assert.equal(snapshotCompatible(a, { ...d, informe_texto: 'Modificado' }), false)
  assert.equal(snapshotCompatible(a, { ...d, archivo: null }), false)
})

test('el borrador conserva su versión base aunque llegue una revisión nueva', () => {
  assert.equal(revisionVigente(0, 0), true)
  assert.equal(revisionVigente(0, 1), false)
  assert.equal(revisionVigente(null, 0), false)
})
