import { useQuery, useQueryClient } from '@tanstack/react-query'
import { obtenerEstudio } from '../../compartido/api/radiologiaApi.js'

/** Detalle del estudio (misma clave en detalle, adquisición, informe e impresión) y cómo actualizarlo. */
export function useEstudioRx(estudioId) {
  const cache = useQueryClient()
  const clave = ['radiologia', 'estudio', String(estudioId)]
  const consulta = useQuery({ queryKey: clave, queryFn: ({ signal }) => obtenerEstudio(estudioId, signal) })
  return { ...consulta, actualizar: dato => cache.setQueryData(clave, dato), recargar: () => cache.invalidateQueries({ queryKey: clave }) }
}

/** Navegación estándar de las pantallas de un estudio: Rayos X / solicitud / estudio / pantalla. */
export function navegacionEstudio(detalle, estudioId, actual) {
  const base = [{ texto: 'Rayos X', ruta: '/rayos-x/gestion' }]
  if (!detalle) return { volverA: '/rayos-x/gestion', textoVolver: 'Volver a Rayos X', migas: [...base, { texto: actual || 'Estudio' }] }
  const solicitud = { texto: detalle.solicitud.referencia, ruta: `/rayos-x/gestion/solicitudes/${detalle.solicitud.id}` }
  const estudio = `/rayos-x/gestion/estudios/${estudioId}`
  return actual
    ? { volverA: estudio, textoVolver: 'Volver al estudio', migas: [...base, solicitud, { texto: detalle.estudio.referencia_estudio, ruta: estudio }, { texto: actual }] }
    : { volverA: '/rayos-x/gestion', textoVolver: 'Volver a Rayos X', migas: [...base, solicitud, { texto: detalle.estudio.referencia_estudio }] }
}
