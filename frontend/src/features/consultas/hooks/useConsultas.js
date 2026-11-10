import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { buscarPacientes, obtenerConsulta, obtenerHistorial, obtenerPaciente } from '../api/consultasApi.js'

export const usePacientes = (buscar, pagina) => useQuery({
  queryKey: ['consultas', 'pacientes', buscar, pagina],
  queryFn: () => buscarPacientes(buscar.trim(), pagina),
  enabled: buscar.trim().length >= 2,
})
export const usePaciente = (id) => useQuery({
  queryKey: ['consultas', 'paciente', id], queryFn: () => obtenerPaciente(id), enabled: Boolean(id),
})
export const useHistorial = (id, pagina, enabled = true) => useQuery({
  queryKey: ['consultas', 'historial', id, pagina],
  queryFn: () => obtenerHistorial(id, pagina), enabled: Boolean(id) && enabled,
})
export const useConsulta = (id) => useQuery({
  queryKey: ['consultas', 'detalle', id], queryFn: () => obtenerConsulta(id), enabled: Boolean(id),
})

export function usePaginaHistorial(id) {
  const [pagina, setPagina] = useState(1)
  useEffect(() => { setPagina(1) }, [id])
  return { pagina, setPagina }
}
