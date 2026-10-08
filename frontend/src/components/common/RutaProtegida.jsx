import { Navigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function RutaProtegida({ children, rolPermitido }) {
  const { usuario, cargando } = useAuth()

  if (cargando) {
    return <div>Cargando sesión...</div>
  }

  if (!usuario) {
    return <Navigate to="/login" replace />
  }

  if (rolPermitido && usuario.rol !== rolPermitido) {
    // Si no tiene el rol, mandarlo al inicio (o mostrar error)
    return <Navigate to="/" replace />
  }

  return children
}
