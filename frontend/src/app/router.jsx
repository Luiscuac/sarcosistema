import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from '../features/accesos/pages/LoginPage.jsx'
import InicioPage from '../features/inicio/pages/InicioPage.jsx'
import LaboratorioPage from '../features/laboratorio/pages/LaboratorioPage.jsx'
import ProtectedRoute from '../features/accesos/auth/ProtectedRoute.jsx'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
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
      </Routes>
    </BrowserRouter>
  )
}
