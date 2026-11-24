import { useEffect, useState } from 'react'

/**
 * Alto disponible en la ventana para un panel fijo (position: sticky): desde donde empieza hoy
 * el panel (o `margen` si ya quedó pegado arriba) hasta el borde inferior. Así el panel entra
 * entero al entrar a la pantalla y al bajar. En pantallas angostas (sin columnas) devuelve null.
 */
export function useAltoDisponible(ref, { margen = 12, minimo = 320, anchoMinimo = 1024 } = {}) {
  const [alto, setAlto] = useState(null)
  useEffect(() => {
    let cuadro = 0
    const medir = () => {
      window.cancelAnimationFrame(cuadro)
      cuadro = window.requestAnimationFrame(() => {
        const nodo = ref.current
        if (!nodo || window.innerWidth < anchoMinimo) { setAlto(null); return }
        const arriba = Math.max(nodo.getBoundingClientRect().top, margen)
        setAlto(Math.max(minimo, Math.floor(window.innerHeight - arriba - margen)))
      })
    }
    medir()
    window.addEventListener('scroll', medir, { passive: true })
    window.addEventListener('resize', medir)
    return () => { window.cancelAnimationFrame(cuadro); window.removeEventListener('scroll', medir); window.removeEventListener('resize', medir) }
  }, [ref, margen, minimo, anchoMinimo])
  return alto
}
