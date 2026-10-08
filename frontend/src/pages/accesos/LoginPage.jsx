import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'
import '../../assets/styles/login.css'

export default function LoginPage() {
  const [identificador, setIdentificador] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState(null)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setError(null)
    
    try {
      const { data } = await api.post('/accesos/login', {
        identificador_acceso: identificador,
        contrasena: contrasena
      })
      
      login({ nombre_usuario: data.nombre_usuario, rol: data.rol }, data.access_token)
      
      if (data.rol === 'laboratorio') {
        navigate('/laboratorio')
      } else {
        navigate('/') // O dashboard general
      }
    } catch (err) {
      if (err.response?.status === 401 || err.response?.status === 403) {
        setError(err.response.data.detail || 'Credenciales incorrectas')
      } else {
        setError('Ocurrió un error al intentar iniciar sesión')
      }
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>SarcoSistema</h1>
        <h2>Iniciar Sesión</h2>
        
        {error && <div className="login-error">{error}</div>}
        
        <form onSubmit={handleLogin} className="login-form">
          <div className="form-group">
            <label htmlFor="identificador">Usuario</label>
            <input
              id="identificador"
              type="text"
              value={identificador}
              onChange={(e) => setIdentificador(e.target.value)}
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="contrasena">Contraseña</label>
            <input
              id="contrasena"
              type="password"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              required
            />
          </div>
          
          <button type="submit" className="login-btn">Entrar</button>
        </form>
      </div>
    </div>
  )
}
