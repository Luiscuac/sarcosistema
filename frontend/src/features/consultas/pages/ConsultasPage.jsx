import { useParams } from 'react-router-dom'
import ConsultasLayout from '../components/ConsultasLayout.jsx'
import ConsultaDetalle from '../components/ConsultaDetalle.jsx'
import PacienteFicha from '../components/PacienteFicha.jsx'
import ConsultaFormulario from '../components/ConsultaFormulario.jsx'
import BusquedaPacientes from './BusquedaPacientes.jsx'
import InformeSolicitudPage from '../../laboratorio/pages/InformeSolicitudPage.jsx'
import InformeEcografiaMedico from '../components/InformeEcografiaMedico.jsx'
import RecetaMedica from '../components/RecetaMedica.jsx'
import RegistrosPublicados from '../../enfermeria/components/RegistrosPublicados.jsx'
import { usePaciente } from '../hooks/useConsultas.js'

function RecetaMedicaRuta({ pacienteId, mode, recetaId }) {
  const paciente = usePaciente(pacienteId)
  if (paciente.isPending) return <p role="status" className="med-message">Cargando paciente…</p>
  if (paciente.isError) return <p role="alert" className="med-message">No se pudo cargar el paciente para la receta.</p>
  return <RecetaMedica paciente={paciente.data} mode={mode} recetaId={recetaId} />
}

function contenidoDeVista(vista, pacienteId, consultaId, recetaId, registroId, usuario) {
  if (vista === 'ficha') return <PacienteFicha id={pacienteId} usuario={usuario} />
  if (vista === 'nueva') return <ConsultaFormulario id={pacienteId} usuario={usuario} />
  if (vista === 'detalle') return <ConsultaDetalle id={consultaId} />
  if (vista === 'informe_laboratorio') return <InformeSolicitudPage modoMedico pacienteId={pacienteId} />
  if (vista === 'receta_nueva') return <RecetaMedicaRuta pacienteId={pacienteId} mode="nueva" />
  if (vista === 'receta_detalle') return <RecetaMedicaRuta pacienteId={pacienteId} mode="detalle" recetaId={recetaId} />
  if (vista === 'enfermeria_detalle') return <RegistrosPublicados pacienteId={pacienteId} registroId={registroId} />
  if (vista === 'informe_ecografia' || vista === 'informe_rayos_x') return <InformeEcografiaMedico />
  return <BusquedaPacientes />
}

export default function ConsultasPage({ usuario, logout, vista = 'busqueda' }) {
  const { pacienteId, consultaId, recetaId, registroId } = useParams()
  return <ConsultasLayout usuario={usuario} logout={logout}>
    {contenidoDeVista(vista, pacienteId, consultaId, recetaId, registroId, usuario)}
  </ConsultasLayout>
}
