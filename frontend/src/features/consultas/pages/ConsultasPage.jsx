import { useParams } from 'react-router-dom'
import ConsultasLayout from '../components/ConsultasLayout.jsx'
import ConsultaDetalle from '../components/ConsultaDetalle.jsx'
import PacienteFicha from '../components/PacienteFicha.jsx'
import ConsultaFormulario from '../components/ConsultaFormulario.jsx'
import BusquedaPacientes from './BusquedaPacientes.jsx'

function contenidoDeVista(vista, pacienteId, consultaId, usuario) {
  if (vista === 'ficha') return <PacienteFicha id={pacienteId} usuario={usuario} />
  if (vista === 'nueva') return <ConsultaFormulario id={pacienteId} usuario={usuario} />
  if (vista === 'detalle') return <ConsultaDetalle id={consultaId} />
  return <BusquedaPacientes />
}

export default function ConsultasPage({ usuario, logout, vista = 'busqueda' }) {
  const { pacienteId, consultaId } = useParams()
  return <ConsultasLayout usuario={usuario} logout={logout}>
    {contenidoDeVista(vista, pacienteId, consultaId, usuario)}
  </ConsultasLayout>
}
