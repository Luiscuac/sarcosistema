import InformeImagenPage from '../../imagenes/components/InformeImagenPage.jsx'
import * as ecografiaApi from '../api/ecografiaApi.js'

export default function InformeEcografiaPage(props) {
  return <InformeImagenPage {...props} modalidad="ecografia" api={ecografiaApi} />
}
