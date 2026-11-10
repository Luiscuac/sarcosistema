import test from 'node:test'
import assert from 'node:assert/strict'
import { destinoDeRol, redireccionDesdeInicio } from './destinos.js'

test('cada rol entra a su módulo y los roles sin módulo van a Inicio', () => {
  assert.equal(destinoDeRol('enfermeria'), '/enfermeria')
  assert.equal(destinoDeRol('farmacia'), '/farmacia')
  assert.equal(destinoDeRol('medico'), '/consultas')
  assert.equal(destinoDeRol('rrhh'), '/inicio')
})

test('Inicio redirige a los roles de un solo módulo, no al médico ni a roles sin módulo', () => {
  assert.equal(redireccionDesdeInicio('enfermeria'), '/enfermeria')
  assert.equal(redireccionDesdeInicio('laboratorio'), '/laboratorio')
  assert.equal(redireccionDesdeInicio('medico'), null)
  assert.equal(redireccionDesdeInicio('rrhh'), null)
})
