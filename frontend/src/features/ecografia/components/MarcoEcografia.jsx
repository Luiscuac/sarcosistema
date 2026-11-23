import BarraSuperior from '../../../shared/ui/BarraSuperior.jsx'
import NavegacionPagina from '../../../shared/ui/NavegacionPagina.jsx'
import '../pages/ecografia.css'

/** Marco común de las pantallas de un estudio: misma barra y navegación que Laboratorio. */
export default function MarcoEcografia({ usuario, logout, navegacion, clase = '', children }) {
  return <main className="lab-page eco-page">
    <div className="lab-main">
      <BarraSuperior usuario={usuario} titulo="Ecografía" inicio="/ecografia" onLogout={logout} />
      <section className={`lab-content ${clase}`.trim()}>
        {navegacion && <NavegacionPagina {...navegacion} />}
        {children}
      </section>
    </div>
  </main>
}

/** Migas: Ecografía / referencia / pantalla actual. */
export function migasEstudio(estudio, actual) {
  const base = [{ texto: 'Ecografía', ruta: '/ecografia' }]
  if (!estudio) return [...base, { texto: actual || 'Estudio' }]
  const ruta = `/ecografia/estudios/${estudio.estudio_id}`
  return actual ? [...base, { texto: estudio.referencia_estudio, ruta }, { texto: actual }] : [...base, { texto: estudio.referencia_estudio }]
}
