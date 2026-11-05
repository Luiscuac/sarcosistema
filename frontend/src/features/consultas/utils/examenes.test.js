import test from 'node:test'
import assert from 'node:assert/strict'
import {
  esDescargable, estadoEstudioImagen, etiquetaArchivo, formatearTamano,
} from './examenes.js'

test('el tamaño se muestra en la unidad legible mas cercana', () => {
  assert.equal(formatearTamano(512), '512 B')
  assert.equal(formatearTamano(1024), '1.0 KB')
  assert.equal(formatearTamano(348), '348 B')
  assert.equal(formatearTamano(5 * 1024 * 1024), '5.0 MB')
  assert.equal(formatearTamano(0), '0 B')
})

test('valores invalidos no inventan un tamaño', () => {
  assert.equal(formatearTamano(undefined), '---')
  assert.equal(formatearTamano(-1), '---')
})

test('las imagenes se pueden previsualizar, DICOM y PDF no', () => {
  assert.equal(esDescargable('image/png'), false)
  assert.equal(esDescargable('image/jpeg'), false)
  assert.equal(esDescargable('application/dicom'), true)
  assert.equal(esDescargable('application/pdf'), true)
})

test('la etiqueta explica por que un archivo no se previsualiza', () => {
  assert.equal(etiquetaArchivo('image/png', 'eco.png'), 'eco.png')
  assert.equal(etiquetaArchivo('application/dicom', 'estudio.dcm'), 'DICOM (descargar)')
  assert.equal(etiquetaArchivo('application/pdf', 'informe.pdf'), 'PDF (descargar)')
})

test('cada estado del estudio tiene texto para el medico', () => {
  assert.equal(estadoEstudioImagen('pendiente_muestra'), 'Pendiente de realizar')
  assert.equal(estadoEstudioImagen('resultado_en_preparacion'), 'Informe en preparación')
  assert.equal(estadoEstudioImagen('publicado'), 'Publicado')
  assert.equal(estadoEstudioImagen('no_realizado'), 'No realizado')
})
