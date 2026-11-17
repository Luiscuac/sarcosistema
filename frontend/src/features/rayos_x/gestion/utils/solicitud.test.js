import test from 'node:test'
import assert from 'node:assert/strict'
import { erroresDeEstudios, prepararEstudiosParaApi } from './solicitud.js'

const catalogo = { estudios: [
  { id: 1, nombre: 'Rodilla', activo: true, config: {
    requiere_lateralidad: true, permite_bilateral: false, detalle_requerido: '',
    protocolos: [{ codigo: 'AP_LAT', proyecciones: ['AP', 'LAT'] }],
    proyecciones: [{ codigo: 'AP' }, { codigo: 'LAT' }],
  } },
  { id: 2, nombre: 'Columna', activo: true, config: {
    requiere_lateralidad: false, permite_bilateral: false, detalle_requerido: 'Segmento',
    protocolos: [], proyecciones: [{ codigo: 'AP' }],
  } },
] }

test('acepta el mismo estudio con lateralidades distintas', () => {
  const valor = [
    { tipo_estudio_id: 1, lateralidad: 'derecha', protocolo: 'AP_LAT', proyecciones: ['AP', 'LAT'] },
    { tipo_estudio_id: 1, lateralidad: 'izquierda', protocolo: 'AP_LAT', proyecciones: ['AP', 'LAT'] },
  ]
  assert.deepEqual(erroresDeEstudios(catalogo, valor), [])
})

test('rechaza duplicados, bilateral no permitido y configuraciones ajenas', () => {
  const valor = [
    { tipo_estudio_id: 1, lateralidad: 'bilateral', proyecciones: ['OBLICUA'] },
    { tipo_estudio_id: 1, lateralidad: 'bilateral', proyecciones: [] },
    { tipo_estudio_id: 2, lateralidad: 'derecha', proyecciones: ['AP'], detalle_region: '' },
  ]
  const errores = erroresDeEstudios(catalogo, valor).join(' ')
  assert.match(errores, /no admite lateralidad bilateral/)
  assert.match(errores, /no puede repetirse/)
  assert.match(errores, /proyecciones/)
  assert.match(errores, /lateralidad no corresponde/)
  assert.match(errores, /completa segmento/)
})

test('normaliza campos opcionales para la API', () => {
  assert.deepEqual(prepararEstudiosParaApi([{
    tipo_estudio_id: '1', lateralidad: '', protocolo: '', proyecciones: [],
    indicacion: '  dolor ', observaciones: ' ', detalle_region: '',
  }]), [{
    tipo_estudio_id: 1, lateralidad: null, protocolo: null, proyecciones: [],
    indicacion: 'dolor', observaciones: null, detalle_region: null,
  }])
})
