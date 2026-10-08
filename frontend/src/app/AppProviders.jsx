import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '../features/accesos/auth/AuthContext.jsx'
import { NotificacionProvider } from '../shared/notifications/NotificationContext.jsx'

const queryClient = new QueryClient()

export default function AppProviders({ children }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <NotificacionProvider>{children}</NotificacionProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
