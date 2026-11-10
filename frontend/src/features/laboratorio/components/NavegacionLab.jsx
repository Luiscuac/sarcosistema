import { Link } from 'react-router-dom'

/**
 * Botón visible para volver a la pantalla anterior y ruta de navegación.
 * `migas`: [{ texto, ruta? }]; la última es la pantalla actual y no lleva enlace.
 */
export default function NavegacionLab({ volverA, textoVolver, migas }) {
  return (
    <div className="lab-nav">
      <Link className="lab-back-button" to={volverA}><span aria-hidden="true">←</span> {textoVolver}</Link>
      <nav className="lab-breadcrumb" aria-label="Ruta">
        {migas.map((miga, indice) => {
          const ultima = indice === migas.length - 1
          return <span key={`${indice}-${miga.texto}`} className="lab-breadcrumb-item">
            {ultima || !miga.ruta ? <span aria-current={ultima ? 'page' : undefined}>{miga.texto}</span> : <Link to={miga.ruta}>{miga.texto}</Link>}
            {!ultima && <span aria-hidden="true" className="lab-breadcrumb-separator">/</span>}
          </span>
        })}
      </nav>
    </div>
  )
}
