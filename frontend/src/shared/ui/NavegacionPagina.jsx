import { Link } from 'react-router-dom'
import './marco.css'

/**
 * Botón visible para volver a la pantalla anterior y ruta de navegación (en todas las pantallas de detalle).
 * Volver: `volverA` (ruta) u `onVolver` (acción, para pantallas que cambian de estado sin cambiar de ruta).
 * `migas`: [{ texto, ruta?, onClick? }]; la última es la pantalla actual y no lleva enlace.
 */
export default function NavegacionPagina({ volverA, onVolver, textoVolver, migas }) {
  const contenidoVolver = <><span aria-hidden="true">←</span> {textoVolver}</>
  return (
    <div className="lab-nav">
      {onVolver
        ? <button type="button" className="lab-back-button" onClick={onVolver}>{contenidoVolver}</button>
        : <Link className="lab-back-button" to={volverA}>{contenidoVolver}</Link>}
      <nav className="lab-breadcrumb" aria-label="Ruta">
        {migas.map((miga, indice) => {
          const ultima = indice === migas.length - 1
          const destino = ultima ? null : miga.ruta ? <Link to={miga.ruta}>{miga.texto}</Link>
            : miga.onClick ? <button type="button" className="lab-breadcrumb-link" onClick={miga.onClick}>{miga.texto}</button> : null
          return <span key={`${indice}-${miga.texto}`} className="lab-breadcrumb-item">
            {destino || <span aria-current={ultima ? 'page' : undefined}>{miga.texto}</span>}
            {!ultima && <span aria-hidden="true" className="lab-breadcrumb-separator">/</span>}
          </span>
        })}
      </nav>
    </div>
  )
}
