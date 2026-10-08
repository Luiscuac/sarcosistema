import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from '../pages/accesos/LoginPage.jsx'
import InicioPage from '../pages/accesos/InicioPage.jsx'
import LaboratorioPage from '../pages/laboratorio/LaboratorioPage.jsx'
import SesionGuard from './SesionGuard.jsx'

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/inicio" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/inicio" element={
          <SesionGuard>
            {({ usuario, logout }) => <InicioPage usuario={usuario} logout={logout} />}
          </SesionGuard>
        } />
        <Route path="/laboratorio" element={
          <SesionGuard rolesPermitidos={['laboratorio']}>
            {({ usuario, logout }) => <LaboratorioPage usuario={usuario} logout={logout} />}
          </SesionGuard>
        } />
      </Routes>
    </BrowserRouter>
  )
}
