import BarraSuperior from '../../../shared/ui/BarraSuperior.jsx'
import NavegacionPagina from '../../../shared/ui/NavegacionPagina.jsx'
import '../../laboratorio/pages/laboratorio.css'
import './rx-tokens.css'

export const RUTA_RAYOS_X = '/rayos-x/gestion'
export const ROL_TECNICO = 'rayos_x'

/**
 * Marco común de las pantallas de gestión de Rayos X: misma barra y navegación que Laboratorio.
 * `navegacion`: { volverA, textoVolver, migas } (opcional; se omite en el panel principal).
 * `ancho`: usa todo el ancho disponible (espacio de trabajo con visor).
 */
export default function RayosXLayout({ usuario, logout, navegacion, ancho = false, children }) {
  return <main className={`lab-page rx-page rx-gestion${ancho ? ' rx-gestion--ancho' : ''}`}>
    <div className="lab-main">
      <BarraSuperior usuario={usuario} titulo="Rayos X" inicio={RUTA_RAYOS_X} onLogout={logout} />
      <section className="lab-content">
        {navegacion && <NavegacionPagina {...navegacion} />}
        {children}
      </section>
    </div>
  </main>
}
