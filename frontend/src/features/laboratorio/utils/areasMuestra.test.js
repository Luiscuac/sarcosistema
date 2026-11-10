import test from 'node:test'
import assert from 'node:assert/strict'
import { areasParaMuestra } from './areasMuestra.js'

const estudios = [
  { estudio_id: 1, categoria_laboratorio: 'hematologia', tipo_estudio_codigo: 'HEMOGRAMA_COMPLETO' },
  { estudio_id: 2, categoria_laboratorio: 'hematologia', tipo_estudio_codigo: 'VES' },
  { estudio_id: 3, categoria_laboratorio: 'bioquimica', tipo_estudio_codigo: 'GLICEMIA' },
  { estudio_id: 4, categoria_laboratorio: 'copro_orina', tipo_estudio_codigo: 'EGO' },
  { estudio_id: 5, categoria_laboratorio: 'copro_orina', tipo_estudio_codigo: 'COPRO_SIMPLE' },
]

test('una muestra de sangre agrupa todos los estudios de cada área', () => {
  assert.deepEqual(areasParaMuestra(estudios, 'Sangre').map((area) => area.estudios.map((estudio) => estudio.estudio_id)), [[1, 2], [3]])
})

test('orina y heces se registran por separado', () => {
  assert.deepEqual(areasParaMuestra(estudios, 'Orina')[0].estudios.map((estudio) => estudio.estudio_id), [4])
  assert.deepEqual(areasParaMuestra(estudios, 'Heces')[0].estudios.map((estudio) => estudio.estudio_id), [5])
})
