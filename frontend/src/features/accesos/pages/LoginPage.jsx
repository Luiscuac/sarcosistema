import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { iniciarSesion, obtenerUsuarioActual } from '../api/accesosApi.js'
import { useAuth } from '../auth/AuthContext.jsx'
import LoginBrand from '../components/LoginBrand.jsx'
import LoginForm from '../components/LoginForm.jsx'
import './LoginPage.css'

export default function LoginPage() {
  const { login, logout } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function iniciarSesionUsuario(credenciales) {
    setError('')
    setEnviando(true)
    let credencialesValidadas = false

    try {
      const sesion = await iniciarSesion(credenciales)
      credencialesValidadas = true
      login(sesion.access_token)

      const perfil = await obtenerUsuarioActual()
      navigate(perfil.rol === 'laboratorio' ? '/laboratorio' : '/inicio', {
        replace: true,
      })
    } catch (err) {
      logout()
      setError(
        credencialesValidadas
          ? 'No se pudo verificar la sesión. Inténtalo de nuevo.'
          : err.response?.status === 401
            ? 'Usuario o contraseña incorrectos.'
            : 'No se pudo iniciar sesión. Inténtalo de nuevo.',
      )
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <LoginBrand />
        <LoginForm
          error={error}
          enviando={enviando}
          onSubmit={iniciarSesionUsuario}
        />
      </div>
    </main>
  )
}
