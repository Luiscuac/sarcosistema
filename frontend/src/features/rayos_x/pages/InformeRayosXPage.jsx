import InformeImagenPage from '../../imagenes/components/InformeImagenPage.jsx'
import * as rayosXApi from '../api/rayosXApi.js'

export default function InformeRayosXPage(props) {
  return <InformeImagenPage {...props} modalidad="rayos_x" api={rayosXApi} />
}
