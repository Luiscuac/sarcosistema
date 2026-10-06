import { useQuery } from '@tanstack/react-query'
import api from '../services/api.js'

export function useResultado(examenId) {
  return useQuery({
    queryKey: ['resultado', examenId],
    queryFn: async () => {
      const { data } = await api.get(`/examenes/${examenId}`)
      return data
    },
    enabled: !!examenId,
  })
}
