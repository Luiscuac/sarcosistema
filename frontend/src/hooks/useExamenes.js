import { useQuery } from '@tanstack/react-query'
import api from '../services/api.js'

export function useExamenes() {
  return useQuery({
    queryKey: ['examenes'],
    queryFn: async () => {
      const { data } = await api.get('/examenes')
      return data
    },
  })
}
