import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext.jsx'
import { obtenerUsuarioActual } from '../api/accesosApi.js'

const SIN_ROLES_RESTRINGIDOS = []

export default function ProtectedRoute({
  children,
  rolesPermitidos = SIN_ROLES_RESTRINGIDOS,
}) {
  const { token, logout } = useAuth()
  const [estado, setEstado] = useState('comprobando')
  const [usuario, setUsuario] = useState(null)

  useEffect(() => {
    let activo = true
    if (!token) {
      setEstado('sin-sesion')
      return () => { activo = false }
    }
    setEstado('comprobando')
    obtenerUsuarioActual().then((data) => {
      if (activo) {
        setUsuario(data)
        setEstado(rolesPermitidos.length === 0 || rolesPermitidos.includes(data.rol)
          ? 'autorizado' : 'sin-permiso')
      }
    }).catch(() => {
      if (activo) {
        logout()
        setEstado('sin-sesion')
      }
    })
    return () => { activo = false }
  }, [token, logout, rolesPermitidos])

  if (!token || estado === 'sin-sesion') return <Navigate to="/login" replace />
  if (estado === 'comprobando') return <main className="session-status">Comprobando sesión…</main>
  if (estado === 'sin-permiso') return (
    <main className="session-status">
      <p>Tu cuenta no tiene acceso a este módulo.</p>
      <button className="primary-button" onClick={logout}>Cerrar sesión</button>
    </main>
  )
  return children({ usuario, logout })
}
