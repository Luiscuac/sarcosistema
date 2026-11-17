import { createBrowserRouter, createRoutesFromElements, Navigate, Route, RouterProvider, useParams } from 'react-router-dom'
import LoginPage from '../features/accesos/pages/LoginPage.jsx'
import InicioPage from '../features/inicio/pages/InicioPage.jsx'
import LaboratorioPage from '../features/laboratorio/pages/LaboratorioPage.jsx'
import SolicitudDetallePage from '../features/laboratorio/pages/SolicitudDetallePage.jsx'
import ResultadoEstudioPage from '../features/laboratorio/pages/ResultadoEstudioPage.jsx'
import AreaResultadosPage from '../features/laboratorio/pages/AreaResultadosPage.jsx'
import InformeSolicitudPage from '../features/laboratorio/pages/InformeSolicitudPage.jsx'
import ProtectedRoute from '../features/accesos/auth/ProtectedRoute.jsx'
import ConsultasPage from '../features/consultas/pages/ConsultasPage.jsx'
import EcografiaPage from '../features/ecografia/pages/EcografiaPage.jsx'
import InformeEcografiaPage from '../features/ecografia/pages/InformeEcografiaPage.jsx'
import PanelRayosXPage from '../features/rayos_x/gestion/pages/PanelRayosXPage.jsx'
import NuevaSolicitudRxPage from '../features/rayos_x/gestion/pages/NuevaSolicitudRxPage.jsx'
import SolicitudRayosXPage from '../features/rayos_x/gestion/pages/SolicitudRayosXPage.jsx'
import HistorialPacienteRxPage from '../features/rayos_x/gestion/pages/HistorialPacienteRxPage.jsx'
import EstudioRayosXPage from '../features/rayos_x/estudio/pages/EstudioRayosXPage.jsx'
import InformeImpresoRxPage from '../features/rayos_x/estudio/pages/InformeImpresoRxPage.jsx'
import EnfermeriaPage from '../features/enfermeria/pages/EnfermeriaPage.jsx'
import EnfermeriaInformePage from '../features/enfermeria/pages/EnfermeriaInformePage.jsx'
import FarmaciaPage from '../features/enfermeria/pages/FarmaciaPage.jsx'
import RayosXPage from '../features/rayos_x/pages/RayosXPage.jsx'
// El personal de Rayos X (rayos_x) se encarga de todo el flujo: solicitud, imágenes e informe.
const ROLES_RAYOS_X = ['rayos_x']

function RedireccionEstudioRx() {
  const { estudioId } = useParams()
  return <Navigate to={`/rayos-x/gestion/estudios/${estudioId}?seccion=informe`} replace />
}

const router = createBrowserRouter(createRoutesFromElements(
  <>
        <Route path="/" element={<Navigate to="/inicio" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/inicio" element={
          <ProtectedRoute>
            {({ usuario, logout }) => <InicioPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
         <Route path="/laboratorio" element={
          <ProtectedRoute rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <LaboratorioPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/laboratorio/solicitudes/:solicitudId" element={
          <ProtectedRoute rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <SolicitudDetallePage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/laboratorio/solicitudes/:solicitudId/estudios/:estudioId/resultado" element={
          <ProtectedRoute rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <ResultadoEstudioPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/laboratorio/solicitudes/:solicitudId/areas/:areaCodigo/resultados" element={
          <ProtectedRoute rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <AreaResultadosPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/laboratorio/solicitudes/:solicitudId/informe" element={
          <ProtectedRoute rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <InformeSolicitudPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        {[
          ['/consultas', 'busqueda'],
          ['/consultas/pacientes/:pacienteId', 'ficha'],
          ['/consultas/pacientes/:pacienteId/nueva', 'nueva'],
          ['/consultas/pacientes/:pacienteId/recetas/nueva', 'receta_nueva'],
          ['/consultas/pacientes/:pacienteId/recetas/:recetaId', 'receta_detalle'],
          ['/consultas/pacientes/:pacienteId/enfermeria/:registroId', 'enfermeria_detalle'],
          ['/consultas/pacientes/:pacienteId/laboratorio/:solicitudId/informe', 'informe_laboratorio'],
          ['/consultas/pacientes/:pacienteId/ecografias/:estudioId/informe', 'informe_ecografia'],
          ['/consultas/pacientes/:pacienteId/rayos-x/:estudioId/informe', 'informe_rayos_x'],
          ['/consultas/:consultaId', 'detalle'],
        ].map(([path, vista]) => <Route key={path} path={path} element={
          <ProtectedRoute rolesPermitidos={['medico']}>
            {({ usuario, logout }) => <ConsultasPage usuario={usuario} logout={logout} vista={vista} />}
          </ProtectedRoute>
        } />)}
        <Route path="/ia" element={
          <Navigate to="/inicio" replace />
        } />
        <Route path="/transcriptor" element={
          <Navigate to="/consultas" replace />
        } />
        <Route path="/ecografia" element={
          <ProtectedRoute rolesPermitidos={['imagenes']}>
            {({ usuario, logout }) => <EcografiaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/ecografia/estudios/:estudioId/informe" element={
          <ProtectedRoute rolesPermitidos={['imagenes']}>
            {({ usuario, logout }) => <InformeEcografiaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        {[
          ['/rayos-x/gestion', PanelRayosXPage],
          ['/rayos-x/gestion/solicitudes/nueva', NuevaSolicitudRxPage],
          ['/rayos-x/gestion/solicitudes/:solicitudId', SolicitudRayosXPage],
          ['/rayos-x/gestion/pacientes/:pacienteId', HistorialPacienteRxPage],
          ['/rayos-x/gestion/estudios/:estudioId', EstudioRayosXPage],
          ['/rayos-x/gestion/estudios/:estudioId/impresion', InformeImpresoRxPage],
        ].map(([path, Pagina]) => <Route key={path} path={path} element={
          <ProtectedRoute rolesPermitidos={ROLES_RAYOS_X}>
            {({ usuario, logout }) => <Pagina usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />)}
        {/* Ruta anterior del informe de texto libre: ahora vive en el espacio de trabajo del estudio. */}
        <Route path="/rayos-x/gestion/estudios/:estudioId/informe" element={<RedireccionEstudioRx />} />
        <Route path="/imagenes" element={<Navigate to="/ecografia" replace />} />
        <Route path="/imagenes/rayos-x-informes" element={<Navigate to="/rayos-x/gestion" replace />} />
        <Route path="/imagenes/estudios/:estudioId/informe" element={
          <ProtectedRoute rolesPermitidos={['imagenes']}>
            {({ usuario, logout }) => <InformeEcografiaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/imagenes/rayos-x" element={
          <ProtectedRoute rolesPermitidos={['medico']}>
            {({ usuario, logout }) => <RayosXPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/enfermeria" element={
          <ProtectedRoute rolesPermitidos={['enfermeria']}>
            {({ usuario, logout }) => <EnfermeriaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/enfermeria/pacientes/:pacienteId/registros/:registroId/informe" element={
          <ProtectedRoute rolesPermitidos={['enfermeria']}>
            {({ usuario, logout }) => <EnfermeriaInformePage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/enfermeria/pacientes/:pacienteId/recetas/:recetaId/informe" element={
          <ProtectedRoute rolesPermitidos={['enfermeria']}>
            {({ usuario, logout }) => <EnfermeriaInformePage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/farmacia" element={
          <ProtectedRoute rolesPermitidos={['farmacia']}>
            {({ usuario, logout }) => <FarmaciaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
  </>
))

export default function AppRouter() {
  return <RouterProvider router={router} />
}
