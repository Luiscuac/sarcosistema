// Mensajes de exito/error globales.
import { createContext, useContext, useState } from 'react'

const NotificacionContext = createContext(null)

export function NotificacionProvider({ children }) {
  const [mensaje, setMensaje] = useState(null)

  const notificar = (texto, tipo = 'info') => setMensaje({ texto, tipo })
  const limpiar = () => setMensaje(null)

  return (
    <NotificacionContext.Provider value={{ mensaje, notificar, limpiar }}>
      {children}
    </NotificacionContext.Provider>
  )
}

export function useNotificacion() {
  return useContext(NotificacionContext)
}
