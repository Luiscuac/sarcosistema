import { useNavigate } from 'react-router-dom'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import NuevaSolicitudRx from '../components/NuevaSolicitudRx.jsx'
import '../gestion.css'

/** Nueva solicitud de Rayos X en pantalla completa: catálogo a la izquierda, pedido y estudios elegidos a la derecha. */
export default function NuevaSolicitudRxPage({ usuario, logout }) {
  const navegar = useNavigate()
  return <RayosXLayout usuario={usuario} logout={logout} clase="rx-trabajo"
    navegacion={{ volverA: '/rayos-x/gestion', textoVolver: 'Volver a estudios', migas: [{ texto: 'Estudios', ruta: '/rayos-x/gestion' }, { texto: 'Nueva solicitud' }] }}>
    <div className="lab-title-row"><div><p className="lab-eyebrow">SOLICITUD DE RAYOS X</p><h1>Nueva solicitud</h1><p className="lab-intro">Identifica al paciente, elige los estudios y completa el pedido.</p></div></div>
    <NuevaSolicitudRx onClose={() => navegar('/rayos-x/gestion')} onCreated={(creada) => navegar(`/rayos-x/gestion/solicitudes/${creada.solicitud_id}`)} />
  </RayosXLayout>
}
