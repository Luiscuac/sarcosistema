import { createContext, useCallback, useContext, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { actualizarSesion } from './sesion.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState(() => sessionStorage.getItem('token'))

  const login = useCallback((accessToken) => {
    actualizarSesion(queryClient, sessionStorage, accessToken)
    setToken(accessToken)
  }, [queryClient])
  const logout = useCallback(() => {
    actualizarSesion(queryClient, sessionStorage, null)
    setToken(null)
  }, [queryClient])

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
