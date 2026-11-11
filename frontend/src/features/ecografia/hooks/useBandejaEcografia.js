import { useQuery } from '@tanstack/react-query'
import { listarBandeja } from '../api/ecografiaApi.js'

export function useBandejaEcografia() {
  return useQuery({ queryKey: ['ecografia', 'bandeja'], queryFn: listarBandeja })
}
