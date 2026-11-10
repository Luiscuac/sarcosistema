import { useCallback, useState } from 'react'

// Solo el nombre del profesional que firma; se separa por cuenta para no mezclar usuarios.
const clave = (usuario) => `laboratorio:responsable:${usuario?.identificador_acceso ?? 'anonimo'}`

function leer(usuario) {
  try { return localStorage.getItem(clave(usuario)) ?? '' } catch { return '' }
}

/** Último responsable usado por esta cuenta; se lee una vez al montar la pantalla. */
export function useResponsableRecordado(usuario) {
  const [recordado] = useState(() => leer(usuario))
  const recordar = useCallback((nombre) => {
    const limpio = String(nombre ?? '').trim()
    if (limpio.length < 2) return
    try { localStorage.setItem(clave(usuario), limpio) } catch { /* almacenamiento no disponible */ }
  }, [usuario])
  return { recordado, recordar }
}
