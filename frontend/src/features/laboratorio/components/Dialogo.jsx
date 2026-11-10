import { useId } from 'react'
import { useDialogo } from '../../../shared/hooks/useDialogo.js'
import './formularios.css'

/** Diálogo modal del laboratorio: Escape, clic fuera y × llaman a onCerrar salvo si está bloqueado. */
export default function Dialogo({ eyebrow, titulo, descripcion, onCerrar, bloqueado = false, compacto = false, children }) {
  const ref = useDialogo(onCerrar, { bloqueado })
  const tituloId = useId()
  const cerrarSiSePuede = () => { if (!bloqueado) onCerrar() }

  return (
    <div className="lab-dialog-backdrop" role="presentation"
      onMouseDown={(evento) => { if (evento.target === evento.currentTarget) cerrarSiSePuede() }}>
      <section ref={ref} tabIndex={-1} className={compacto ? 'lab-dialog lab-dialog--compacto' : 'lab-dialog'}
        role="dialog" aria-modal="true" aria-labelledby={tituloId}>
        <header className="lab-dialog-header">
          <div>
            {eyebrow && <p className="lab-eyebrow">{eyebrow}</p>}
            <h2 id={tituloId}>{titulo}</h2>
            {descripcion && <p>{descripcion}</p>}
          </div>
          <button className="lab-dialog-close" type="button" onClick={cerrarSiSePuede} disabled={bloqueado} aria-label="Cerrar">×</button>
        </header>
        {children}
      </section>
    </div>
  )
}
