import { createBrowserRouter, createRoutesFromElements, Navigate, Route, RouterProvider } from 'react-router-dom'
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
import RayosXImagenesPage from '../features/rayos_x/pages/RayosXImagenesPage.jsx'
import InformeRayosXPage from '../features/rayos_x/pages/InformeRayosXPage.jsx'
import EnfermeriaPage from '../features/enfermeria/pages/EnfermeriaPage.jsx'
import FarmaciaPage from '../features/enfermeria/pages/FarmaciaPage.jsx'
import RayosXPage from '../features/rayos_x/pages/RayosXPage.jsx'
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
        <Route path="/rayos-x/gestion" element={
          <ProtectedRoute rolesPermitidos={['rayos_x']}>
            {({ usuario, logout }) => <RayosXImagenesPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/rayos-x/gestion/estudios/:estudioId/informe" element={
          <ProtectedRoute rolesPermitidos={['rayos_x']}>
            {({ usuario, logout }) => <InformeRayosXPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
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
