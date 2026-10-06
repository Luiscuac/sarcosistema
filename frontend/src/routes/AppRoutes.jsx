// Todas las rutas de la app.
import { BrowserRouter, Routes, Route } from 'react-router-dom'

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<div>SarcoSistema</div>} />
        {/* TODO: rutas por modulo, protegidas segun rol (ver AuthContext) */}
      </Routes>
    </BrowserRouter>
  )
}
