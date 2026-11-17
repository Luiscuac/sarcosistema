import { useEffect, useState } from 'react'
import Dialogo from '../../../laboratorio/components/Dialogo.jsx'
import VisorRadiografia from '../../components/VisorRadiografia.jsx'
import { obtenerVistaImagen } from '../../api/radiologiaApi.js'

export function useVistaImagen(archivoId) {
  const [url, setUrl] = useState(null)
  useEffect(() => {
    if (!archivoId) return undefined
    let vigente = true
    let creada
    obtenerVistaImagen(archivoId).then(blob => {
      creada = URL.createObjectURL(blob)
      if (vigente) setUrl(creada)
      else URL.revokeObjectURL(creada)
    }).catch(() => { if (vigente) setUrl(null) })
    return () => { vigente = false; if (creada) URL.revokeObjectURL(creada) }
  }, [archivoId])
  return url
}

function Miniatura({ imagen, proyecciones, editable, ocupado, onAsignar, onRetirar, onAbrir }) {
  const url = useVistaImagen(imagen.archivo_id)
  return <article className="rxe-miniatura">
    <button type="button" className="rxe-miniatura-imagen" onClick={() => onAbrir(imagen)} disabled={!url}>
      {url ? <img src={url} alt={`Vista de ${imagen.nombre_original}`} /> : <span>Cargando vista...</span>}
    </button>
    <div><strong>{imagen.nombre_original}</strong><small>{(imagen.tamano_bytes / 1024 / 1024).toFixed(1)} MB · {new Date(imagen.fecha_carga).toLocaleString('es-BO')}</small></div>
    <label>Proyeccion<select value={imagen.proyeccion_codigo || ''} disabled={!editable || ocupado} onChange={e => onAsignar(imagen.id, e.target.value || null)}>
      <option value="">Sin asignar</option>{proyecciones.map(p => <option key={p.codigo} value={p.codigo}>{p.nombre}</option>)}
    </select></label>
    {editable && <button type="button" className="lab-secondary-button" onClick={() => onRetirar(imagen)}>Retirar</button>}
  </article>
}

function VisorDialogo({ imagen, onCerrar }) {
  const url = useVistaImagen(imagen.archivo_id)
  return <Dialogo titulo={imagen.nombre_original} onCerrar={onCerrar}>
    <div className="lab-dialog-body rxe-visor-dialogo">{url ? <VisorRadiografia url={url} alt={imagen.nombre_original} vision={undefined} mapa={null} onMapa={() => {}} /> : <p>Cargando imagen...</p>}</div>
  </Dialogo>
}

export default function GaleriaImagenes({ imagenes, proyecciones, editable, ocupado, onAsignar, onRetirar }) {
  const [visor, setVisor] = useState(null)
  const [retirar, setRetirar] = useState(null)
  const [motivo, setMotivo] = useState('')
  return <>
    <div className="rxe-galeria">{imagenes.length ? imagenes.map(imagen => <Miniatura key={imagen.id} imagen={imagen} proyecciones={proyecciones}
      editable={editable} ocupado={ocupado} onAsignar={onAsignar} onRetirar={setRetirar} onAbrir={setVisor} />) : <p>No hay imagenes adjuntas.</p>}</div>
    {visor && <VisorDialogo imagen={visor} onCerrar={() => setVisor(null)} />}
    {retirar && <Dialogo compacto eyebrow="CONFIRMAR" titulo="Retirar imagen" bloqueado={ocupado} onCerrar={() => { setRetirar(null); setMotivo('') }}>
      <div className="lab-dialog-body lab-confirm-body"><p>La imagen quedara retirada con trazabilidad; el archivo no se borrara.</p>
        <label className="lab-search-label">Motivo *<textarea required value={motivo} onChange={e => setMotivo(e.target.value)} /></label>
        {!motivo.trim() && <p className="lab-form-hint">Escribe el motivo para continuar.</p>}</div>
      <footer className="lab-dialog-footer"><button type="button" disabled={ocupado} onClick={() => { setRetirar(null); setMotivo('') }}>Volver</button><button type="button" className="lab-incidence-submit" disabled={ocupado || !motivo.trim()} onClick={() => onRetirar(retirar.id, motivo, () => { setRetirar(null); setMotivo('') })}>{ocupado ? 'Procesando...' : 'Retirar imagen'}</button></footer>
    </Dialogo>}
  </>
}
