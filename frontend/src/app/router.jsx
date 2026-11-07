import { createBrowserRouter, createRoutesFromElements, Navigate, Route, RouterProvider } from 'react-router-dom'
import LoginPage from '../features/accesos/pages/LoginPage.jsx'
import InicioPage from '../features/inicio/pages/InicioPage.jsx'
import LaboratorioPage from '../features/laboratorio/pages/LaboratorioPage.jsx'
import SolicitudDetallePage from '../features/laboratorio/pages/SolicitudDetallePage.jsx'
import ResultadoEstudioPage from '../features/laboratorio/pages/ResultadoEstudioPage.jsx'
import AreaResultadosPage from '../features/laboratorio/pages/AreaResultadosPage.jsx'
import InformeSolicitudPage from '../features/laboratorio/pages/InformeSolicitudPage.jsx'
import IaPage from '../features/ia/whisper/pages/IaPage.jsx'
import ProtectedRoute from '../features/accesos/auth/ProtectedRoute.jsx'
import ConsultasPage from '../features/consultas/pages/ConsultasPage.jsx'
import ImagenesPage from '../features/imagenes/pages/ImagenesPage.jsx'
import EnfermeriaPage from '../features/enfermeria/pages/EnfermeriaPage.jsx'
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
          ['/consultas/:consultaId', 'detalle'],
        ].map(([path, vista]) => <Route key={path} path={path} element={
          <ProtectedRoute rolesPermitidos={['medico']}>
            {({ usuario, logout }) => <ConsultasPage usuario={usuario} logout={logout} vista={vista} />}
          </ProtectedRoute>
        } />)}
        <Route path="/ia" element={
          <ProtectedRoute>
            {({ usuario, logout }) => <IaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/transcriptor" element={
          <Navigate to="/consultas" replace />
        } />
        <Route path="/imagenes" element={
          <ProtectedRoute rolesPermitidos={['imagenes']}>
            {({ usuario, logout }) => <ImagenesPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
        <Route path="/enfermeria" element={
          <ProtectedRoute rolesPermitidos={['enfermeria']}>
            {({ usuario, logout }) => <EnfermeriaPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
  </>
))

export default function AppRouter() {
  return <RouterProvider router={router} />
}
