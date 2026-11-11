import BandejaEstudios from '../../imagenes/components/BandejaEstudios.jsx'
import { useBandejaRayosX } from '../hooks/useBandejaRayosX.js'

export default function RayosXImagenesPage(props) {
  const bandeja = useBandejaRayosX()
  return <BandejaEstudios {...props} modalidad="rayos_x" bandeja={bandeja} />
}
