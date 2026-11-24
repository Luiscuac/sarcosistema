import BarraSuperior from '../../../shared/ui/BarraSuperior.jsx'
import NavegacionPagina from '../../../shared/ui/NavegacionPagina.jsx'
import './rx-tokens.css'

export const RUTA_RAYOS_X = '/rayos-x/gestion'

/**
 * Marco común de las pantallas de gestión de Rayos X: misma barra y navegación que Laboratorio.
 * `navegacion`: { volverA, textoVolver, migas } (opcional; se omite en el panel principal).
 * `clase`: clase de la página, como en Laboratorio (lab-detail-page, lab-area-results-page…);
 * `rx-trabajo` usa todo el ancho para el espacio de trabajo con la placa.
 */
export default function RayosXLayout({ usuario, logout, navegacion, clase = '', children }) {
  return <main className="lab-page rx-page rx-gestion">
    <div className="lab-main">
      <BarraSuperior usuario={usuario} titulo="Rayos X" inicio={RUTA_RAYOS_X} onLogout={logout} />
      <section className={`lab-content ${clase}`.trim()}>
        {navegacion && <NavegacionPagina {...navegacion} />}
        {children}
      </section>
    </div>
  </main>
}
