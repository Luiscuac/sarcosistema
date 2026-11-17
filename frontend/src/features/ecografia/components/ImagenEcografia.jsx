import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { obtenerArchivoImagen } from '../api/ecografiaApi.js'

export default function ImagenEcografia({ archivo, local = false }) {
  const [url, setUrl] = useState('')
  const consulta = useQuery({ queryKey: ['ecografia', 'adjunto', archivo.id], queryFn: () => obtenerArchivoImagen(archivo.id), enabled: !local })
  const blob = local ? archivo : consulta.data
  useEffect(() => {
    if (!blob) return undefined
    const u = URL.createObjectURL(blob); setUrl(u)
    return () => URL.revokeObjectURL(u)
  }, [blob])
  if (!url) return <p role={consulta.isError ? 'alert' : 'status'}>{consulta.isError ? 'No se pudo cargar la imagen.' : 'Cargando imagen…'}</p>
  return <figure className="eco-imagen"><img src={url} alt={archivo.nombre_original || archivo.name} /><figcaption>{archivo.nombre_original || archivo.name}</figcaption></figure>
}

