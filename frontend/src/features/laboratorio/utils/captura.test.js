import test from 'node:test'
import assert from 'node:assert/strict'
import { agruparPorSeccion, motivoPublicacionBloqueada, parametrosVisibles, resumenCaptura } from './captura.js'

const parametros = [
  { id: 1, codigo: 'hb', nombre: 'Hemoglobina', obligatorio: true, tipo_entrada: 'decimal', rango_referencia: '11.0 a 16.0 g/dL', seccion: 'Serie roja' },
  { id: 2, codigo: 'hto', nombre: 'Hematocrito', obligatorio: true, tipo_entrada: 'decimal', rango_referencia: '37 a 54 %', seccion: 'Serie roja' },
  { id: 3, codigo: 'obs', nombre: 'Aspecto', obligatorio: false, tipo_entrada: 'texto', rango_referencia: null, seccion: null },
  { id: 4, codigo: 'unidad_reportada', nombre: 'Unidad', obligatorio: false, tipo_entrada: 'texto', rango_referencia: null, seccion: null },
]

test('oculta el parámetro técnico y agrupa por sección en orden', () => {
  const visibles = parametrosVisibles(parametros)
  assert.equal(visibles.length, 3)
  assert.deepEqual(agruparPorSeccion(visibles).map(([seccion, items]) => [seccion, items.length]), [['Serie roja', 2], ['Resultado', 1]])
})

test('resume avance, obligatorios faltantes y valores fuera de rango', () => {
  const resumen = resumenCaptura(parametrosVisibles(parametros), { 1: '9.0', 2: ' ', 3: 'Claro' })
  assert.equal(resumen.total, 3)
  assert.equal(resumen.completos, 2)
  assert.deepEqual(resumen.faltantes, ['Hematocrito'])
  assert.deepEqual(resumen.fueraDeRango, [{ id: 1, nombre: 'Hemoglobina', valor: '9.0', estado: 'bajo' }])
})

test('explica el primer motivo que impide publicar', () => {
  const base = { hayCambios: false, responsable: 'Ana Pérez', faltantes: [], sinBorrador: false }
  assert.equal(motivoPublicacionBloqueada(base), null)
  assert.match(motivoPublicacionBloqueada({ ...base, hayCambios: true }), /cambios sin guardar/)
  assert.match(motivoPublicacionBloqueada({ ...base, sinBorrador: true }), /Guarda un borrador/)
  assert.match(motivoPublicacionBloqueada({ ...base, responsable: ' ' }), /responsable/)
  assert.equal(motivoPublicacionBloqueada({ ...base, faltantes: ['Hb', 'Hto'] }), 'Faltan campos obligatorios: Hb, Hto.')
})
