import { useEffect, useRef, useState } from 'react'
import { mapasDisponibles } from '../analisis.js'

const ZOOM_MIN = 1
const ZOOM_MAX = 6
const limitar = (valor, min, max) => Math.min(max, Math.max(min, valor))
const pct = valor => `${(valor * 100).toFixed(3)}%`

const icono = d => <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{d}</svg>
const ICONOS = {
  mas: icono(<><path d="M12 5v14" /><path d="M5 12h14" /></>),
  menos: icono(<path d="M5 12h14" />),
  sol: icono(<><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></>),
  invertir: icono(<><circle cx="12" cy="12" r="9" /><path d="M12 3v18" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" /></>),
  reiniciar: icono(<><path d="M3 12a9 9 0 1 0 3-6.7" /><path d="M3 4v5h5" /></>),
}

/** Visor de radiografía: zoom, desplazamiento, brillo/contraste, inversión y capa de mapa de calor. */
export default function VisorRadiografia({ url, alt, vision, mapa, onMapa }) {
  const [zoom, setZoom] = useState(1)
  const [desplazamiento, setDesplazamiento] = useState({ x: 0, y: 0 })
  const [brillo, setBrillo] = useState(100)
  const [contraste, setContraste] = useState(100)
  const [invertir, setInvertir] = useState(false)
  const [opacidad, setOpacidad] = useState(55)
  const arrastre = useRef(null)
  const lienzo = useRef(null)
  const mapas = mapasDisponibles(vision)
  const region = vision?.mapas_calor?.region
  const actual = mapa && vision?.mapas_calor?.mapas?.[mapa]
  const zona = actual?.zona

  const cambiarZoom = factor => setZoom(z => {
    const nuevo = limitar(z * factor, ZOOM_MIN, ZOOM_MAX)
    if (nuevo === 1) setDesplazamiento({ x: 0, y: 0 })
    return nuevo
  })
  useEffect(() => {
    // Listener nativo no pasivo: React registra "wheel" como pasivo y no permite evitar el scroll.
    const nodo = lienzo.current
    if (!nodo) return undefined
    const rueda = e => { e.preventDefault(); cambiarZoom(e.deltaY < 0 ? 1.15 : 0.87) }
    nodo.addEventListener('wheel', rueda, { passive: false })
    return () => nodo.removeEventListener('wheel', rueda)
  })
  const reiniciar = () => { setZoom(1); setDesplazamiento({ x: 0, y: 0 }); setBrillo(100); setContraste(100); setInvertir(false) }
  const inicio = e => {
    if (zoom === 1) return
    e.currentTarget.setPointerCapture?.(e.pointerId)
    arrastre.current = { x: e.clientX - desplazamiento.x, y: e.clientY - desplazamiento.y }
  }
  const mover = e => { if (arrastre.current) setDesplazamiento({ x: e.clientX - arrastre.current.x, y: e.clientY - arrastre.current.y }) }
  const fin = () => { arrastre.current = null }

  return <div className="rx-visor">
    <div className="rx-visor-barra" role="toolbar" aria-label="Herramientas del visor">
      <div className="rx-visor-grupo" aria-label="Zoom">
        <button type="button" className="rx-visor-btn" onClick={() => cambiarZoom(0.8)} aria-label="Alejar" title="Alejar">{ICONOS.menos}</button>
        <span className="rx-visor-zoom" aria-live="polite">{Math.round(zoom * 100)} %</span>
        <button type="button" className="rx-visor-btn" onClick={() => cambiarZoom(1.25)} aria-label="Acercar" title="Acercar">{ICONOS.mas}</button>
      </div>
      <details className="rx-visor-ajustes">
        <summary className="rx-visor-btn es-texto" title="Brillo y contraste">{ICONOS.sol}<span>Ajustes</span></summary>
        <div className="rx-visor-pop">
          <label>Brillo<input type="range" min="40" max="200" value={brillo} onChange={e => setBrillo(Number(e.target.value))} /></label>
          <label>Contraste<input type="range" min="40" max="300" value={contraste} onChange={e => setContraste(Number(e.target.value))} /></label>
        </div>
      </details>
      <button type="button" className="rx-visor-btn es-texto" aria-pressed={invertir} onClick={() => setInvertir(v => !v)} title="Invertir grises">{ICONOS.invertir}<span>Invertir</span></button>
      <button type="button" className="rx-visor-btn" onClick={reiniciar} aria-label="Restablecer vista" title="Restablecer vista">{ICONOS.reiniciar}</button>
      {mapas.length > 0 && <div className="rx-visor-grupo rx-visor-mapa-ctl">
        <label><span>Mapa de calor</span><select value={mapa || ''} onChange={e => onMapa(e.target.value || null)}>
          <option value="">Ninguno</option>
          {mapas.map(m => <option key={m.clave} value={m.clave}>{m.etiqueta}</option>)}
        </select></label>
        {mapa && <label title="Opacidad del mapa"><span className="rx-sr">Opacidad</span><input type="range" min="10" max="90" value={opacidad} onChange={e => setOpacidad(Number(e.target.value))} /></label>}
      </div>}
    </div>
    <div ref={lienzo} className={`rx-visor-lienzo${zoom > 1 ? ' es-movible' : ''}`}
      onPointerDown={inicio} onPointerMove={mover} onPointerUp={fin} onPointerLeave={fin}
      onDoubleClick={reiniciar}>
      <div className="rx-visor-capa" style={{ transform: `translate(${desplazamiento.x}px, ${desplazamiento.y}px) scale(${zoom})` }}>
        <img src={url} alt={alt} draggable="false"
          style={{ filter: `brightness(${brillo}%) contrast(${contraste}%)${invertir ? ' invert(1)' : ''}` }} />
        {actual && region && <img className="rx-visor-mapa" alt="" aria-hidden="true" draggable="false"
          src={`data:image/png;base64,${actual.png_base64}`}
          style={{ left: pct(region.x), top: pct(region.y), width: pct(region.ancho), height: pct(region.alto), opacity: opacidad / 100 }} />}
        {zona && region && <div className="rx-visor-zona" aria-hidden="true"
          style={{ left: pct(region.x + zona.x * region.ancho), top: pct(region.y + zona.y * region.alto),
            width: pct(zona.ancho * region.ancho), height: pct(zona.alto * region.alto) }} />}
      </div>
    </div>
    <p className="rx-visor-ayuda">Rueda del ratón: zoom · arrastrar: mover · doble clic: restablecer.{mapa ? ` El mapa muestra dónde se apoyó el modelo${vision?.mapas_calor?.restringido_a_pulmones ? ' (limitado a los campos pulmonares)' : ''}, no la ubicación confirmada de una lesión.` : ''}</p>
  </div>
}
