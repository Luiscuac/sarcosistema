import test from 'node:test'
import assert from 'node:assert/strict'
import {
  detectarCambios, estadoInicialInforme, fraseTecnicaDesdeAdquisicion, insertarFrase,
  limpiarContenido, parametrosANumeros, partirTextoInforme, validarArchivoImagen,
} from './informe.js'

test('inicializa la plantilla sin rellenar frases', () => {
  const estado = estadoInicialInforme(null, { generales: [{ clave: 'conclusion' }], apartados: [{ clave: 'huesos' }] })
  assert.deepEqual(estado.contenido, { generales: { conclusion: '' }, apartados: { huesos: '' } })
})

test('limpia vacios y detecta cambios semanticos', () => {
  const inicial = { contenido: { generales: { conclusion: '' }, apartados: {} }, textoFinal: null }
  assert.deepEqual(limpiarContenido(inicial.contenido), { generales: {}, apartados: {} })
  assert.equal(detectarCambios({ ...inicial, contenido: { generales: { conclusion: ' normal ' }, apartados: {} } }, inicial), true)
})

test('inserta frases sin ejecutarlas automáticamente', () => {
  assert.equal(insertarFrase('', 'Sin fractura.'), 'Sin fractura.')
  assert.equal(insertarFrase('Alineacion conservada', 'Sin fractura.'), 'Alineacion conservada. Sin fractura.')
})

test('compone técnica con nombres del catálogo', () => {
  const frase = fraseTecnicaDesdeAdquisicion({
    estudio: { tipo_estudio_nombre: 'Radiografia de rodilla', detalle: { lateralidad: 'derecha' } },
    config: { proyecciones: [{ codigo: 'AP', nombre: 'AP' }, { codigo: 'LAT', nombre: 'lateral' }] },
    adquisicion: { proyecciones_realizadas: ['AP', 'LAT'] },
  })
  assert.equal(frase, 'Radiografia de rodilla. Proyecciones AP y lateral, lateralidad derecha.')
})

test('convierte parámetros y omite vacios', () => {
  assert.deepEqual(parametrosANumeros({ kvp: '60', mas: '', equipo: ' Sala 1 ' }), { kvp: 60, equipo: 'Sala 1' })
})

test('valida formatos y limites de archivos', () => {
  assert.equal(validarArchivoImagen({ name: 'placa.png', type: 'image/png', size: 10 }), null)
  assert.match(validarArchivoImagen({ name: 'nota.pdf', type: 'application/pdf', size: 10 }), /Formato/)
  assert.match(validarArchivoImagen({ name: 'placa.dcm', type: '', size: 101 * 1024 * 1024 }), /100 MB/)
})

test('parte titulos en mayusculas para impresión', () => {
  assert.deepEqual(partirTextoInforme('TÉCNICA:\nDos proyecciones.\n\nCONCLUSION:\nSin lesion.'), [
    { titulo: 'TÉCNICA', lineas: ['Dos proyecciones.', ''] },
    { titulo: 'CONCLUSIÓN', lineas: ['Sin lesión.'] },
  ])
})
