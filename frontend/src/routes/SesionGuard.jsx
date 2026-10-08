import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import api from '../services/api.js'

export default function SesionGuard({ children, rolesPermitidos = [] }) {
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
    api.get('/accesos/yo').then(({ data }) => {
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
  }, [token])

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
