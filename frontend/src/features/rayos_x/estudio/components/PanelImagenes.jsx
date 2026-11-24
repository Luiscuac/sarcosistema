import { useEffect, useRef, useState } from 'react'
import VisorRadiografia from '../../asistente/components/VisorRadiografia.jsx'
import { useVistaImagen } from './GaleriaImagenes.jsx'

function BotonMiniatura({ imagen, activa, onClick }) {
  const url = useVistaImagen(imagen.archivo_id)
  return <button type="button" role="tab" aria-selected={activa} className={`rxe-tira-item${activa ? ' is-active' : ''}`} onClick={onClick}>
    {url ? <img src={url} alt="" /> : <span>...</span>}<small>{imagen.proyeccion_codigo || 'Sin asignar'}</small>
  </button>
}

/** Placa grande a la izquierda con tira de miniaturas (informe y adquisición). */
export default function PanelImagenes({ imagenes }) {
  const [indice, setIndice] = useState(0); const tira = useRef(null)
  useEffect(() => { if (indice >= imagenes.length) setIndice(Math.max(0, imagenes.length - 1)) }, [imagenes.length, indice])
  const seleccionada = imagenes[indice]; const url = useVistaImagen(seleccionada?.archivo_id)
  const teclado = e => { if (!['ArrowLeft', 'ArrowRight'].includes(e.key) || !imagenes.length) return; e.preventDefault(); setIndice(i => e.key === 'ArrowRight' ? (i + 1) % imagenes.length : (i - 1 + imagenes.length) % imagenes.length) }
  return <aside className="rxe-work-visor"><div ref={tira} className="rxe-tira" role="tablist" aria-label="Imágenes del estudio" onKeyDown={teclado}>
    {imagenes.map((imagen, i) => <BotonMiniatura key={imagen.id} imagen={imagen} activa={i === indice} onClick={() => setIndice(i)} />)}
  </div><div className="rxe-visor-principal">{seleccionada && url ? <VisorRadiografia url={url} alt={seleccionada.nombre_original} vision={undefined} mapa={null} onMapa={() => {}} /> : <p role={url === false ? 'alert' : undefined}>{imagenes.length ? (url === false ? 'No se pudo cargar la imagen.' : 'Cargando imagen…') : 'No hay imágenes disponibles.'}</p>}</div></aside>
}
