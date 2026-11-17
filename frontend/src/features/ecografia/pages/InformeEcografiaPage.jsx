import { lazy, Suspense } from 'react'

const EditorEcografia = lazy(() => import('../components/EditorEcografia.jsx'))

export default function InformeEcografiaPage(props) {
  return <Suspense fallback={<p role="status">Cargando editor de ecografía…</p>}><EditorEcografia {...props} /></Suspense>
}
