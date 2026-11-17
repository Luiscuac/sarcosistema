import BandejaEcografia from '../components/BandejaEcografia.jsx'
import { useBandejaEcografia } from '../hooks/useBandejaEcografia.js'
import { useState } from 'react'
import NuevaSolicitudEcografia from '../components/NuevaSolicitudEcografia.jsx'
import './ecografia.css'

export default function EcografiaPage(props) {
  const bandeja = useBandejaEcografia()
  const [nueva, setNueva] = useState(false)
  const [creada, setCreada] = useState(null)
  const [ciclo, setCiclo] = useState(0)
  function solicitudCreada(solicitud) {
    setCreada(solicitud)
    setCiclo(actual => actual + 1)
  }
  return <><BandejaEcografia {...props} key={ciclo} bandeja={bandeja} creada={creada} onCerrarAviso={() => setCreada(null)} onNueva={() => setNueva(true)} />{nueva && <NuevaSolicitudEcografia onCerrar={() => setNueva(false)} onCreada={solicitudCreada} />}</>
}
