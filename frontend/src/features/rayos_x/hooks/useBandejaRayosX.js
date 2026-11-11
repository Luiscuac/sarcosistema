import { useQuery } from '@tanstack/react-query'
import { listarBandeja } from '../api/rayosXApi.js'

export function useBandejaRayosX() {
  return useQuery({ queryKey: ['rayos_x', 'bandeja'], queryFn: listarBandeja })
}
