import { createBrowserRouter, createRoutesFromElements, Navigate, Route, RouterProvider } from 'react-router-dom'
import LoginPage from '../features/accesos/pages/LoginPage.jsx'
import InicioPage from '../features/inicio/pages/InicioPage.jsx'
import LaboratorioPage from '../features/laboratorio/pages/LaboratorioPage.jsx'
import IaPage from '../features/ia/whisper/pages/IaPage.jsx'
import ProtectedRoute from '../features/accesos/auth/ProtectedRoute.jsx'
import TranscriptorPage from '../features/ia/transporter/pages/TranscriptorPage.jsx'
import ConsultasPage from '../features/consultas/pages/ConsultasPage.jsx'
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
        {[
          ['/consultas', 'busqueda'],
          ['/consultas/pacientes/:pacienteId', 'ficha'],
          ['/consultas/pacientes/:pacienteId/nueva', 'nueva'],
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
          <ProtectedRoute>
            {({ usuario, logout }) => <TranscriptorPage usuario={usuario} logout={logout} />}
          </ProtectedRoute>
        } />
  </>
))

export default function AppRouter() {
  return <RouterProvider router={router} />
}
