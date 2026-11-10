import { useEffect, useState } from 'react'

/** Marca de tiempo que se renueva periódicamente para textos como "hace 5 min". */
export function useAhora(intervalo = 60000) {
  const [ahora, setAhora] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), intervalo)
    return () => clearInterval(id)
  }, [intervalo])
  return ahora
}
