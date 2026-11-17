import test from 'node:test'
import assert from 'node:assert/strict'
import { destinoDeRol, redireccionDesdeInicio } from './destinos.js'

test('cada rol entra a su módulo y los roles sin módulo van a Inicio', () => {
  assert.equal(destinoDeRol('enfermeria'), '/enfermeria')
  assert.equal(destinoDeRol('farmacia'), '/farmacia')
  assert.equal(destinoDeRol('medico'), '/consultas')
  assert.equal(destinoDeRol('rrhh'), '/inicio')
})

test('Inicio lleva al médico a Consultas y a cada rol a su área disponible', () => {
  assert.equal(redireccionDesdeInicio('enfermeria'), '/enfermeria')
  assert.equal(redireccionDesdeInicio('laboratorio'), '/laboratorio')
  assert.equal(redireccionDesdeInicio('medico'), '/consultas')
  assert.equal(redireccionDesdeInicio('imagenes'), '/ecografia')
  assert.equal(redireccionDesdeInicio('rayos_x'), '/rayos-x/gestion')
  assert.equal(redireccionDesdeInicio('farmacia'), '/farmacia')
  assert.equal(redireccionDesdeInicio('rrhh'), null)
})
