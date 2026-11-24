import { useEffect, useRef, useState } from 'react'
import VisorRadiografia from '../../asistente/components/VisorRadiografia.jsx'
import { useVistaImagen } from './GaleriaImagenes.jsx'
import { useAltoDisponible } from '../../../../shared/hooks/useAltoDisponible.js'

function BotonMiniatura({ imagen, activa, onClick }) {
  const url = useVistaImagen(imagen.archivo_id)
  return <button type="button" role="tab" aria-selected={activa} className={`rxe-tira-item${activa ? ' is-active' : ''}`} onClick={onClick}>
    {url ? <img src={url} alt="" /> : <span>...</span>}<small>{imagen.proyeccion_codigo || 'Sin asignar'}</small>
  </button>
}

/**
 * Placa grande a la izquierda con tira de miniaturas (informe y adquisición).
 * Se ajusta al alto libre de la ventana para verse siempre entera. `vacio`: qué mostrar sin imágenes
 * (en la adquisición, la zona para subirlas: es el primer paso).
 */
export default function PanelImagenes({ imagenes, vacio = null }) {
  const [indice, setIndice] = useState(0); const tira = useRef(null); const panel = useRef(null)
  const alto = useAltoDisponible(panel)
  useEffect(() => { if (indice >= imagenes.length) setIndice(Math.max(0, imagenes.length - 1)) }, [imagenes.length, indice])
  const seleccionada = imagenes[indice]; const url = useVistaImagen(seleccionada?.archivo_id)
  const teclado = e => { if (!['ArrowLeft', 'ArrowRight'].includes(e.key) || !imagenes.length) return; e.preventDefault(); setIndice(i => e.key === 'ArrowRight' ? (i + 1) % imagenes.length : (i - 1 + imagenes.length) % imagenes.length) }
  if (!imagenes.length && vacio) return <aside ref={panel} className="rxe-work-visor rxe-visor-vacio" style={alto ? { height: alto } : undefined}>{vacio}</aside>
  return <aside ref={panel} className="rxe-work-visor" style={alto ? { height: alto } : undefined}><div ref={tira} className="rxe-tira" role="tablist" aria-label="Imágenes del estudio" onKeyDown={teclado}>
    {imagenes.map((imagen, i) => <BotonMiniatura key={imagen.id} imagen={imagen} activa={i === indice} onClick={() => setIndice(i)} />)}
  </div><div className="rxe-visor-principal">{seleccionada && url ? <VisorRadiografia url={url} alt={seleccionada.nombre_original} vision={undefined} mapa={null} onMapa={() => {}} /> : <p role={url === false ? 'alert' : undefined}>{imagenes.length ? (url === false ? 'No se pudo cargar la imagen.' : 'Cargando imagen…') : 'No hay imágenes disponibles.'}</p>}</div></aside>
}
