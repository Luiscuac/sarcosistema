import { Link } from 'react-router-dom'
import '../pages/consultas.css'

export default function ConsultasLayout({ usuario, logout, children, area = 'consultas' }) {
  const rayosX = area === 'rayos-x'
  return <main className={`med-page${rayosX ? ' rx-page' : ''}`}>
    <aside className="med-sidebar">
      <div className="med-sidebar-heading"><strong>SarcoSistema</strong><span>{rayosX ? 'RAYOS X · TÓRAX' : 'CONSULTA MÉDICA'}</span></div>
      <nav aria-label="Módulo médico">
        {rayosX ? <>
          <span className="med-nav-active" aria-current="page">Rayos X</span>
          <Link to="/consultas">Consulta médica</Link>
        </> : <>
          <Link className="med-nav-active" aria-current="page" to="/consultas">Pacientes y consultas</Link>
          <Link to="/imagenes/rayos-x">Rayos X</Link>
        </>}
      </nav>
      <button className="med-signout" type="button" onClick={logout}>Cerrar sesión</button>
    </aside>
    <div className="med-main">
      <header className="med-topbar"><span>{rayosX ? 'ESTUDIOS RADIOLÓGICOS' : 'CONSULTA EXTERNA'}</span><div><span className="med-session">● Sesión activa</span><strong>{usuario.identificador_acceso}</strong></div></header>
      <section className="med-content">{children}</section>
    </div>
  </main>
}
