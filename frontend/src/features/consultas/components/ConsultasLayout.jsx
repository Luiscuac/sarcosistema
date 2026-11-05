import { Link } from 'react-router-dom'
import '../pages/consultas.css'

export default function ConsultasLayout({ usuario, logout, children }) {
  return <main className="med-page">
    <aside className="med-sidebar">
      <div className="med-sidebar-heading"><strong>SarcoSistema</strong><span>CONSULTA MÉDICA</span></div>
      <nav aria-label="Módulo médico"><Link className="med-nav-active" to="/consultas">Pacientes y consultas</Link><Link to="/inicio">Inicio</Link></nav>
      <button className="med-signout" onClick={logout}>Cerrar sesión</button>
    </aside>
    <div className="med-main">
      <header className="med-topbar"><span>CONSULTA EXTERNA</span><div><span className="med-session">● Sesión activa</span><strong>{usuario.identificador_acceso}</strong></div></header>
      <section className="med-content">{children}</section>
    </div>
  </main>
}
