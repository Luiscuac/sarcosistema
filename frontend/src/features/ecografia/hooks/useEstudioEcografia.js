import { useQuery } from '@tanstack/react-query'
import { obtenerEstudio } from '../api/ecografiaApi.js'

/** Un estudio de ecografía (misma clave de caché en detalle, registro e informe). */
export function useEstudioEcografia(estudioId) {
  return useQuery({ queryKey: ['ecografia', 'estudio', Number(estudioId)], queryFn: () => obtenerEstudio(estudioId) })
}

/** Usa plantilla por órganos; si no, el estudio usa el informe de texto libre heredado. */
export const usaPlantilla = estudio => Boolean(estudio.organos?.length)
  && !(estudio.informe?.estado === 'publicado' && !estudio.informe.datos_ecografia)
