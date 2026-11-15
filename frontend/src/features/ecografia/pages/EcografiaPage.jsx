import BandejaEstudios from '../../imagenes/components/BandejaEstudios.jsx'
import { useBandejaEcografia } from '../hooks/useBandejaEcografia.js'
import { useState } from 'react'
import NuevaSolicitudEcografia from '../components/NuevaSolicitudEcografia.jsx'
import './ecografia.css'

export default function EcografiaPage(props) {
  const bandeja = useBandejaEcografia()
  const [nueva, setNueva] = useState(false)
  return <><BandejaEstudios {...props} modalidad="ecografia" bandeja={bandeja} accion={<button type="button" className="primary-button" onClick={() => setNueva(true)}>+ Nueva solicitud</button>} />{nueva && <NuevaSolicitudEcografia onCerrar={() => setNueva(false)} />}</>
}
