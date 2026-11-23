import React from 'react'
import ReactDOM from 'react-dom/client'
import '@fontsource/inter/latin-400.css'
import '@fontsource/inter/latin-600.css'
// Base de estilos antes que las pantallas: así cada pantalla puede ajustar la base (mismo orden que antes del refactor).
import './shared/styles/tokens.css'
import './shared/styles/formularios.css'
import './shared/styles/pantallas.css'
import App from './app/App.jsx'
import AppProviders from './app/AppProviders.jsx'
import './shared/styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProviders>
      <App />
    </AppProviders>
  </React.StrictMode>,
)
