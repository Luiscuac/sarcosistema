import { useEffect, useRef } from 'react'

const ENFOCABLES = 'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'

/**
 * Comportamiento accesible de un diálogo modal: Escape cierra, el foco queda
 * dentro mientras está abierto y vuelve al elemento que lo abrió al cerrarse.
 */
export function useDialogo(onCerrar, { bloqueado = false } = {}) {
  const ref = useRef(null)
  const cerrar = useRef(onCerrar)
  const bloqueo = useRef(bloqueado)
  // Se captura en el primer render, antes de que un autoFocus mueva el foco.
  const anterior = useRef(document.activeElement)
  cerrar.current = onCerrar
  bloqueo.current = bloqueado

  useEffect(() => {
    const dialogo = ref.current
    // Respeta un autoFocus de React; si no lo hay, enfoca el primer control.
    if (dialogo && !dialogo.contains(document.activeElement)) {
      (dialogo.querySelector(ENFOCABLES) ?? dialogo).focus()
    }

    function alPresionar(evento) {
      if (evento.key === 'Escape' && !bloqueo.current) {
        evento.stopPropagation()
        cerrar.current()
        return
      }
      if (evento.key !== 'Tab' || !dialogo) return
      const enfocables = [...dialogo.querySelectorAll(ENFOCABLES)]
      if (!enfocables.length) return
      const primero = enfocables[0]
      const ultimo = enfocables.at(-1)
      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault()
        ultimo.focus()
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault()
        primero.focus()
      }
    }

    dialogo?.addEventListener('keydown', alPresionar)
    return () => {
      dialogo?.removeEventListener('keydown', alPresionar)
      anterior.current?.focus?.()
    }
  }, [])

  return ref
}
