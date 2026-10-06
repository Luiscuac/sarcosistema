import { useState } from 'react'
import api from '../../services/api.js'

export default function FormularioExamen({ pacienteId, onCreado }) {
  const [tipo, setTipo] = useState('')

  const enviar = async (e) => {
    e.preventDefault()
    const { data } = await api.post('/examenes', { paciente_id: pacienteId, tipo })
    onCreado?.(data)
  }

  return (
    <form onSubmit={enviar}>
      <input value={tipo} onChange={(e) => setTipo(e.target.value)} placeholder="Tipo de examen" />
      <button type="submit">Crear</button>
    </form>
  )
}
