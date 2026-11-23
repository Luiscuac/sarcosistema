import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import NavegacionLab from '../../laboratorio/components/NavegacionLab.jsx'
import '../../laboratorio/pages/laboratorio.css'
import '../../laboratorio/components/formularios.css'
import '../pages/ecografia.css'

/** Marco común de las pantallas de un estudio: misma barra y navegación que Laboratorio. */
export default function MarcoEcografia({ usuario, logout, navegacion, clase = '', children }) {
  return <main className="lab-page eco-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo="Ecografía" inicio="/ecografia" onLogout={logout} />
      <section className={`lab-content ${clase}`.trim()}>
        {navegacion && <NavegacionLab {...navegacion} />}
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
