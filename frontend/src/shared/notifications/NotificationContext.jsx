// Mensajes breves de éxito/error, visibles en cualquier pantalla.
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import './notificaciones.css'

const NotificacionContext = createContext(null)
const DURACION_MS = 5000

export function NotificacionProvider({ children }) {
  const [mensaje, setMensaje] = useState(null)

  const notificar = useCallback((texto, tipo = 'info') => setMensaje({ texto, tipo, id: Date.now() }), [])
  const limpiar = useCallback(() => setMensaje(null), [])

  useEffect(() => {
    if (!mensaje) return undefined
    const temporizador = setTimeout(limpiar, DURACION_MS)
    return () => clearTimeout(temporizador)
  }, [mensaje, limpiar])

  const valor = useMemo(() => ({ mensaje, notificar, limpiar }), [mensaje, notificar, limpiar])

  return (
    <NotificacionContext.Provider value={valor}>
      {children}
      <div className="notificaciones" role={mensaje?.tipo === 'error' ? 'alert' : 'status'} aria-live="polite">
        {mensaje && <div key={mensaje.id} className={`notificacion notificacion--${mensaje.tipo}`}>
          <span>{mensaje.texto}</span>
          <button type="button" onClick={limpiar} aria-label="Cerrar aviso">×</button>
        </div>}
      </div>
    </NotificacionContext.Provider>
  )
}

export function useNotificacion() {
  return useContext(NotificacionContext)
}
