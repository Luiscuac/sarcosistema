import { useQuery } from '@tanstack/react-query'
import { listarBandeja } from '../api/imagenesApi.js'

export function useBandeja() {
  return useQuery({
    queryKey: ['imagenes', 'bandeja'],
    queryFn: listarBandeja,
  })
}
