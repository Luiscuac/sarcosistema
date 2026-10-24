import { useQuery } from '@tanstack/react-query'
import { obtenerExamen } from '../api/laboratorioApi.js'

export function useResultado(examenId) {
  return useQuery({
    queryKey: ['resultado', examenId],
    queryFn: () => obtenerExamen(examenId),
    enabled: !!examenId,
  })
}
