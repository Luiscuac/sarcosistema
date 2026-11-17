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

test('bandeja: urgente primero, luego índice visual y finalmente antigüedad', async () => {
  const { ordenarBandeja } = await import('./analisis.js')
  const e = (id, prioridad, indice, dia) => ({ estudio_id: id, prioridad, fecha_solicitud: `2026-11-${String(dia).padStart(2, '0')}T10:00:00Z`, triaje: indice === null ? null : { indice } })
  const lista = [e(1, 'sin_prioridad', 0.2, 10), e(2, 'sin_prioridad', 0.9, 12), e(3, 'urgente', null, 14), e(4, 'sin_prioridad', null, 9)]
  assert.deepEqual(ordenarBandeja(lista).map(x => x.estudio_id), [3, 2, 1, 4])
  assert.deepEqual(ordenarBandeja(lista, 'llegada').map(x => x.estudio_id), [3, 4, 1, 2])
})

test('detecta triaje pendiente para refrescar la bandeja', async () => {
  const { triajeEnProceso } = await import('./analisis.js')
  assert.equal(triajeEnProceso([{ triaje: { estado: 'en_proceso' } }]), true)
  assert.equal(triajeEnProceso([{ triaje: null }, { triaje: { estado: 'completado' } }]), false)
})

test('resultados antiguos con 3 categorías siguen mostrándose', async () => {
  const { hallazgosDeVision, mapasDisponibles } = await import('./analisis.js')
  const viejo = hallazgosDeVision({ findings: [{ name: 'Effusion', score: 0.7 }, { name: 'Consolidation', score: 0.1 }] })
  assert.equal(viejo.completo, false)
  assert.deepEqual(viejo.todas.map(h => [h.name, h.above_operating_point]), [['Effusion', true], ['Consolidation', false]])
  assert.deepEqual(mapasDisponibles({}), [])
  const nuevo = hallazgosDeVision({ all_findings: [{ name: 'Nodule', score: 0.8, above_operating_point: true }, { name: 'Effusion', score: 0.2 }] })
  assert.equal(nuevo.completo, true)
  assert.deepEqual(nuevo.principales.map(h => h.name), ['Effusion'])
  assert.deepEqual(mapasDisponibles({ mapas_calor: { mapas: { indice_pulmonar: {}, Nodule: {} } } }).map(m => m.etiqueta), ['Índice pulmonar', 'Nódulo'])
})

test('avisos del informe: discrepancias, luego omisiones y coincidencias; compatibles con resultados antiguos', async () => {
  const { avisosDeFusion, mencionesDelInforme } = await import('./analisis.js')
  const fusion = {
    discrepancias: [{ hallazgo: 'Effusion', score: 0.6 }],
    coincidencias: [{ hallazgo: 'Mass', score: 0.9, tipo: 'coincidencia' }],
    posibles_omisiones: [{ hallazgo: 'Nodule', score: 0.8, tipo: 'posible_omision' }],
    informe: { Effusion: { estado: 'negado', evidencia: ['No se observa derrame'] }, Nodule: { estado: 'no_mencionado', evidencia: [] } },
  }
  assert.deepEqual(avisosDeFusion(fusion).map(a => [a.tipo, a.hallazgo]), [['discrepancia', 'Effusion'], ['posible_omision', 'Nodule'], ['coincidencia', 'Mass']])
  assert.deepEqual(mencionesDelInforme(fusion).map(m => m.nombre), ['Effusion'])
  assert.deepEqual(avisosDeFusion({}), [])
})

test('lectura del médico y porcentajes del panel', async () => {
  const { lecturaAnormal, porcentaje } = await import('./analisis.js')
  assert.equal(lecturaAnormal('si'), true)
  assert.equal(lecturaAnormal('no'), false)
  assert.equal(lecturaAnormal(''), null)
  assert.equal(porcentaje(0.456), '46 %')
  assert.equal(porcentaje(null), '—')
})

import { nivelSenal } from './analisis.js'

test('nivel de señal en lenguaje simple', () => {
  assert.equal(nivelSenal(0.9).clave, 'alta')
  assert.equal(nivelSenal(0.6).clave, 'moderada')
  assert.equal(nivelSenal(0.52).clave, 'limite')
  assert.equal(nivelSenal(0.2).clave, 'baja')
  assert.equal(nivelSenal(undefined).clave, 'sin_dato')
})

import { sugerenciasDeVision } from './analisis.js'

test('sugerencias: tres principales por score y el resto como débiles', () => {
  const h = (name, score) => ({ name, score, above_operating_point: score >= 0.5 })
  const vision = { all_findings: [h('A', 0.6), h('B', 0.9), h('C', 0.55), h('D', 0.7), h('E', 0.2)] }
  const { principales, debiles, sinSenal } = sugerenciasDeVision(vision)
  assert.deepEqual(principales.map(x => x.name), ['B', 'D', 'A'])
  assert.deepEqual(debiles.map(x => x.name), ['C'])
  assert.deepEqual(sinSenal.map(x => x.name), ['E'])
})
