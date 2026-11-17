import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import NavegacionLab from '../../laboratorio/components/NavegacionLab.jsx'
import '../../laboratorio/pages/laboratorio.css'
import '../pages/rx-tokens.css'

export const RUTA_RAYOS_X = '/rayos-x/gestion'
export const ROL_TECNICO = 'rayos_x'
export const ROL_RADIOLOGO = 'radiologo'

/**
 * Marco común de las pantallas de gestión de Rayos X: misma barra y navegación que Laboratorio.
 * `navegacion`: { volverA, textoVolver, migas } (opcional; se omite en el panel principal).
 * `ancho`: usa todo el ancho disponible (espacio de trabajo con visor).
 */
export default function RayosXLayout({ usuario, logout, navegacion, ancho = false, children }) {
  return <main className={`lab-page rx-page rx-gestion${ancho ? ' rx-gestion--ancho' : ''}`}>
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo="Rayos X" inicio={RUTA_RAYOS_X} onLogout={logout} />
      <section className="lab-content">
        {navegacion && <NavegacionLab {...navegacion} />}
        {children}
      </section>
    </div>
  </main>
}
