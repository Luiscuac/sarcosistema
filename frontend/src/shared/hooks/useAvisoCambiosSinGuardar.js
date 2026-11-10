import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'

const MENSAJE = 'Hay cambios sin guardar. ¿Quieres salir y descartarlos?'

/** Pide confirmación antes de salir de la pantalla (navegación interna o cierre de pestaña). */
export function useAvisoCambiosSinGuardar(hayCambios) {
  const blocker = useBlocker(({ currentLocation, nextLocation }) =>
    hayCambios && currentLocation.pathname !== nextLocation.pathname)

  useEffect(() => {
    if (blocker.state !== 'blocked') return
    if (window.confirm(MENSAJE)) blocker.proceed()
    else blocker.reset()
  }, [blocker])

  useEffect(() => {
    if (!hayCambios) return undefined
    const avisar = (evento) => { evento.preventDefault(); evento.returnValue = '' }
    window.addEventListener('beforeunload', avisar)
    return () => window.removeEventListener('beforeunload', avisar)
  }, [hayCambios])
}
