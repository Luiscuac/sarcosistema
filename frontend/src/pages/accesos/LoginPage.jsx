import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import api from '../../services/api.js'
import './login.css'

export default function LoginPage() {
  const { login, logout } = useAuth()
  const navigate = useNavigate()
  const [identificador, setIdentificador] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(event) {
    event.preventDefault()
    setError('')
    setEnviando(true)
    let credencialesValidadas = false
    try {
      const { data } = await api.post('/accesos/login', {
        identificador_acceso: identificador,
        password,
      })
      credencialesValidadas = true
      login(data.access_token)
      const perfil = await api.get('/accesos/yo')
      navigate(perfil.data.rol === 'laboratorio' ? '/laboratorio' : '/inicio', { replace: true })
    } catch (err) {
      logout()
      setError(credencialesValidadas
        ? 'No se pudo verificar la sesión. Inténtalo de nuevo.'
        : err.response?.status === 401
          ? 'Usuario o contraseña incorrectos.'
          : 'No se pudo iniciar sesión. Inténtalo de nuevo.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <div className="auth-brand">
          <span className="auth-brand-mark" aria-hidden="true">S</span>
          <h1>SarcoSistema</h1>
          <p>Sistema de exámenes complementarios</p>
        </div>
        <form className="auth-form" onSubmit={enviar}>
          <div className="auth-form-heading">
            <h2>Iniciar sesión</h2>
            <p>Ingresa con tu cuenta personal para acceder a tus funciones.</p>
          </div>
          <div className="auth-field">
            <label htmlFor="identificador">Usuario *</label>
            <input id="identificador" autoComplete="username" value={identificador}
              onChange={(event) => setIdentificador(event.target.value)} placeholder="Identificador de acceso"
              required />
          </div>
          <div className="auth-field">
            <label htmlFor="password">Contraseña *</label>
            <input id="password" type="password" autoComplete="current-password" value={password}
              onChange={(event) => setPassword(event.target.value)} placeholder="Ingresa tu contraseña"
              required />
          </div>
          {error && <p className="auth-error" role="alert">{error}</p>}
          <button className="primary-button auth-submit" type="submit" disabled={enviando}>
            {enviando ? 'Ingresando…' : 'Ingresar'}
          </button>
          <p className="auth-help">Si no tienes acceso, contacta al responsable del sistema.</p>
        </form>
        <p className="auth-footnote">SarcoSistema · Prototipo en evaluación</p>
      </div>
    </main>
  )
}
