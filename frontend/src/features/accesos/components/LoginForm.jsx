import { useState } from 'react'
import LoginCredentialsFields from './LoginCredentialsFields.jsx'
import './LoginForm.css'

export default function LoginForm({ error, enviando, onSubmit }) {
  const [credenciales, setCredenciales] = useState({
    identificador_acceso: '',
    password: '',
  })

  function cambiarCredencial(campo, valor) {
    setCredenciales((actuales) => ({ ...actuales, [campo]: valor }))
  }

  function enviar(event) {
    event.preventDefault()
    onSubmit(credenciales)
  }

  return (
    <form className="auth-form" onSubmit={enviar}>
      <div className="auth-form-heading">
        <h2>Iniciar sesión</h2>
        <p>Ingresa con tu cuenta personal para acceder a tus funciones.</p>
      </div>
      <LoginCredentialsFields
        credenciales={credenciales}
        onChange={cambiarCredencial}
      />
      {error && <p className="auth-error" role="alert">{error}</p>}
      <button className="primary-button auth-submit" type="submit" disabled={enviando}>
        {enviando ? 'Ingresando…' : 'Ingresar'}
      </button>
      <p className="auth-help">Si no tienes acceso, contacta al responsable del sistema.</p>
    </form>
  )
}
