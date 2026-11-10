import { useEffect, useState } from 'react'

/** Devuelve el valor cuando deja de cambiar durante `espera` ms (evita una consulta por tecla). */
export function useValorDiferido(valor, espera = 300) {
  const [diferido, setDiferido] = useState(valor)
  useEffect(() => {
    const temporizador = setTimeout(() => setDiferido(valor), espera)
    return () => clearTimeout(temporizador)
  }, [valor, espera])
  return diferido
}
