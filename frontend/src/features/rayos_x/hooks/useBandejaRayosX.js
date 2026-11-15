import { useQuery } from '@tanstack/react-query'
import { listarBandeja } from '../api/rayosXApi.js'
import { triajeEnProceso } from '../analisis.js'

export function useBandejaRayosX() {
  return useQuery({ queryKey: ['rayos_x', 'bandeja'], queryFn: listarBandeja,
    // Mientras la IA analiza radiografías recién subidas, se refresca la bandeja.
    refetchInterval: consulta => triajeEnProceso(consulta.state.data) ? 5000 : false })
}
