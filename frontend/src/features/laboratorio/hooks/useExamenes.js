import { useQuery } from '@tanstack/react-query'
import { listarExamenes, listarResultadosPublicados } from '../api/laboratorioApi.js'

// La bandeja se comparte entre varias personas: se actualiza sola cada 45 s.
const ACTUALIZACION_MS = 45000

export function useExamenes() {
  return useQuery({
    queryKey: ['examenes'],
    queryFn: listarExamenes,
    refetchInterval: ACTUALIZACION_MS,
  })
}

export function useExamenesFinalizados(habilitado) {
  return useQuery({
    queryKey: ['examenes', 'publicados'],
    queryFn: listarResultadosPublicados,
    enabled: habilitado,
    refetchInterval: ACTUALIZACION_MS,
  })
}
