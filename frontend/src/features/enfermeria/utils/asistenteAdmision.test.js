import test from 'node:test'
import assert from 'node:assert/strict'
import { parchesAdmision, textoPropuesta } from './asistenteAdmision.js'

test('convierte propuestas numéricas a campos de admisión sin signosVitales', () => {
  assert.deepEqual(parchesAdmision({ campo: 'temperatura_c', valor: 38.5 }, {}), { temperatura_c: '38.5' })
  assert.deepEqual(parchesAdmision({ campo: 'dolor_escala', valor: 8 }, {}), { dolor_escala: '8' })
  assert.equal(textoPropuesta({ campo: 'saturacion_oxigeno', valor: 96 }), '96 %')
})

test('combina presión sistólica y diastólica en el campo de admisión', () => {
  const form = { presion: '118/76' }
  assert.deepEqual(parchesAdmision({ campo: 'presion_sistolica', valor: 120 }, form), { presion: '120/76' })
  assert.deepEqual(parchesAdmision({ campo: 'presion_diastolica', valor: 80 }, form), { presion: '118/80' })
})

test('mapea observaciones del modelo al campo narrativo de enfermería', () => {
  assert.deepEqual(parchesAdmision({ campo: 'observaciones', valor: 'Paciente tranquilo' }, {}),
    { observaciones_enfermeria: 'Paciente tranquilo' })
})
