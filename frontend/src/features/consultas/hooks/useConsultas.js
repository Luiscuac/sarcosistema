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
export const useHistorial = (id, pagina) => useQuery({
  queryKey: ['consultas', 'historial', id, pagina],
  queryFn: () => obtenerHistorial(id, pagina), enabled: Boolean(id),
})
export const useConsulta = (id) => useQuery({
  queryKey: ['consultas', 'detalle', id], queryFn: () => obtenerConsulta(id), enabled: Boolean(id),
})
