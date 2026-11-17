import test from 'node:test'
import assert from 'node:assert/strict'
import { agruparInformePorArea, filasDeEstudio, fueraDeRango, resumenParaCopiar } from './informe.js'

const parametro = (nombre, valor, extra = {}) => ({ nombre, valor, unidad: null, rango_referencia: null, seccion: null, ...extra })

test('un estudio de un solo valor ocupa una sola fila con el nombre del estudio', () => {
  const filas = filasDeEstudio({ nombre: 'Glucosa', parametros: [parametro('Resultado', '95', { unidad: 'mg/dL' })] })
  assert.equal(filas.length, 1)
  assert.equal(filas[0].parametro.nombre, 'Glucosa')
  assert.equal(filas[0].parametro.unidad, 'mg/dL')
})

test('la sección y el parámetro genéricos "Resultado" no duplican filas', () => {
  const filas = filasDeEstudio({
    nombre: 'Creatinina',
    parametros: [parametro('Resultado', '0.9', { seccion: 'Resultado', unidad: 'mg/dL', rango_referencia: '0.6-1.2' })],
  })
  assert.deepEqual(filas.map((fila) => fila.tipo), ['parametro'])
  assert.equal(filas[0].parametro.nombre, 'Creatinina')
})

test('el formato libre antiguo integra la unidad capturada en la misma fila', () => {
  const filas = filasDeEstudio({
    nombre: 'PCR',
    parametros: [
      parametro('Resultado', 'Negativo', { seccion: 'Resultado' }),
      parametro('Unidad (si aplica)', 'mg/L', { seccion: 'Resultado' }),
    ],
  })
  assert.equal(filas.length, 1)
  assert.equal(filas[0].parametro.nombre, 'PCR')
  assert.equal(filas[0].parametro.unidad, 'mg/L')
})

test('varios parámetros bajo la sección genérica no muestran subtítulo', () => {
  const filas = filasDeEstudio({
    nombre: 'Perfil lipídico',
    parametros: [parametro('Colesterol', '180', { seccion: 'Resultado' }), parametro('HDL', '50', { seccion: 'Resultado' })],
  })
  assert.deepEqual(filas.map((fila) => fila.tipo), ['estudio', 'parametro', 'parametro'])
})

test('un estudio de un solo valor conserva el nombre del parámetro si aporta información', () => {
  const [fila] = filasDeEstudio({ nombre: 'Grupo sanguíneo', parametros: [parametro('Factor Rh', 'Positivo')] })
  assert.equal(fila.parametro.nombre, 'Grupo sanguíneo · Factor Rh')
})

test('un estudio con varias secciones lleva título y subsecciones en la misma tabla', () => {
  const filas = filasDeEstudio({
    nombre: 'Hemograma',
    parametros: [
      parametro('Hematíes', '4.8', { seccion: 'Serie roja' }),
      parametro('Hemoglobina', '14', { seccion: 'Serie roja' }),
      parametro('Leucocitos', '7000', { seccion: 'Serie blanca' }),
    ],
  })
  assert.deepEqual(filas.map((fila) => fila.tipo), ['estudio', 'seccion', 'parametro', 'parametro', 'seccion', 'parametro'])
})

test('un estudio sin parámetros queda como fila vacía', () => {
  assert.deepEqual(filasDeEstudio({ nombre: 'Cultivo', parametros: [] }), [{ tipo: 'vacio', nombre: 'Cultivo' }])
})

test('agrupa por área en orden de aparición, sin repetir observaciones ni responsables', () => {
  const areas = agruparInformePorArea([
    { categoria: 'quimica', nombre: 'Glucosa', observaciones: 'Muestra en ayunas', responsable_publicacion: 'Ana', parametros: [parametro('Glucosa', '95', { rango_referencia: '70-110' })] },
    { categoria: 'hematologia', nombre: 'Hematocrito', observaciones: '', responsable_publicacion: 'Luis', parametros: [parametro('Hematocrito', '42')] },
    { categoria: 'quimica', nombre: 'Urea', observaciones: 'Muestra en ayunas', responsable_publicacion: 'Ana', parametros: [parametro('Urea', '30')] },
  ])
  assert.deepEqual(areas.map((area) => area.categoria), ['quimica', 'hematologia'])
  assert.equal(areas[0].filas.length, 2)
  assert.deepEqual(areas[0].observaciones, ['Muestra en ayunas'])
  assert.deepEqual(areas[0].responsables, ['Ana'])
  assert.equal(areas[0].tieneReferencia, true)
  assert.equal(areas[1].tieneReferencia, false)
  assert.equal(areas[1].tieneUnidad, false)
})

test('solo marca fuera de rango valores numéricos', () => {
  assert.equal(fueraDeRango(parametro('Glucosa', '150', { rango_referencia: '70-110' })), true)
  assert.equal(fueraDeRango(parametro('Glucosa', '95', { rango_referencia: '70-110' })), false)
  assert.equal(fueraDeRango(parametro('Aspecto', 'Turbio', { rango_referencia: '70-110' })), false)
})

test('el resumen para copiar usa una línea por área y marca valores fuera de rango', () => {
  const texto = resumenParaCopiar({
    referencia: 'SOL-1',
    resultados: [
      { categoria: 'bioquimica', nombre: 'Creatinina', parametros: [parametro('Resultado', '0.9', { seccion: 'Resultado', unidad: 'mg/dL', rango_referencia: '0.6-1.3' })] },
      { categoria: 'bioquimica', nombre: 'Urea', parametros: [parametro('Resultado', '66', { seccion: 'Resultado', unidad: 'mg/dL', rango_referencia: '10-50' })] },
      { categoria: 'serologia', nombre: 'HAI para Chagas', observaciones: 'Repetir', parametros: [parametro('Resultado', 'Negativo')] },
    ],
    estudios_no_realizados: [{ nombre: 'Coprocultivo', motivo: 'muestra_insuficiente' }],
  }, { nombreArea: (codigo) => codigo.toUpperCase(), fecha: '12/11/2026' })
  assert.equal(texto, [
    'Laboratorio SOL-1 (12/11/2026):',
    '- BIOQUIMICA: Creatinina: 0.9 mg/dL, Urea: 66 mg/dL (alto).',
    '- SEROLOGIA: HAI para Chagas: Negativo. Obs.: Repetir',
    '- No realizados: Coprocultivo (muestra_insuficiente).',
  ].join('\n'))
})
