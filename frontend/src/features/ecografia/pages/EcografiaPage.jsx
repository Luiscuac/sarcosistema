import BandejaEstudios from '../../imagenes/components/BandejaEstudios.jsx'
import { useBandejaEcografia } from '../hooks/useBandejaEcografia.js'

export default function EcografiaPage(props) {
  const bandeja = useBandejaEcografia()
  return <BandejaEstudios {...props} modalidad="ecografia" bandeja={bandeja} />
}
