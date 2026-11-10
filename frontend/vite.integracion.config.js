// Prueba local aislada: no cambia CORS ni los servidores del checkout original.
// VITE_API_URL=/api npm run dev -- --config vite.integracion.config.js --strictPort
import base from './vite.config.js'

export default {
  ...base,
  server: {
    ...base.server,
    host: 'localhost',
    port: 5187,
    proxy: {
      '/api': {
        target: 'http://localhost:8017',
        rewrite: path => path.replace(/^\/api/, ''),
      },
    },
  },
}
