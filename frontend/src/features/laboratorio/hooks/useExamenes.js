import { useQuery } from '@tanstack/react-query'
import { listarExamenes } from '../api/laboratorioApi.js'

export function useExamenes() {
  return useQuery({
    queryKey: ['examenes'],
    queryFn: listarExamenes,
  })
}
