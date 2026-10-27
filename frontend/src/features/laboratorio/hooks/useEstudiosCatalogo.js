import { useQuery } from '@tanstack/react-query'
import { listarEstudiosCatalogo } from '../api/laboratorioApi.js'

export function useEstudiosCatalogo() {
  return useQuery({
    queryKey: ['laboratorio', 'catalogo-estudios'],
    queryFn: listarEstudiosCatalogo,
  })
}
