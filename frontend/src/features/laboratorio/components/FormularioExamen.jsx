import { useState } from 'react'
import { crearExamen } from '../api/laboratorioApi.js'

export default function FormularioExamen({ pacienteId, onCreado }) {
  const [tipo, setTipo] = useState('')

  const enviar = async (e) => {
    e.preventDefault()
    const examen = await crearExamen({ paciente_id: pacienteId, tipo })
    onCreado?.(examen)
  }

  return (
    <form onSubmit={enviar}>
      <input value={tipo} onChange={(e) => setTipo(e.target.value)} placeholder="Tipo de examen" />
      <button type="submit">Crear</button>
    </form>
  )
}
