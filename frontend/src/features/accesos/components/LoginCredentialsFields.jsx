export default function LoginCredentialsFields({ credenciales, onChange }) {
  return (
    <>
      <div className="auth-field">
        <label htmlFor="identificador">Usuario *</label>
        <input
          id="identificador"
          autoComplete="username"
          value={credenciales.identificador_acceso}
          onChange={(event) => onChange('identificador_acceso', event.target.value)}
          placeholder="Identificador de acceso"
          required
        />
      </div>
      <div className="auth-field">
        <label htmlFor="password">Contraseña *</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={credenciales.password}
          onChange={(event) => onChange('password', event.target.value)}
          placeholder="Ingresa tu contraseña"
          required
        />
      </div>
    </>
  )
}
