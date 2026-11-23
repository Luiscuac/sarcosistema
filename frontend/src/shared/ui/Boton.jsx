import { Link } from 'react-router-dom'

const CLASES = { primario: 'primary-button', secundario: 'lab-secondary-button' }

/** Clase de un botón estándar (para enlaces u otros elementos con aspecto de botón). */
export const claseBoton = (variante = 'primario', extra = '') => [CLASES[variante], extra].filter(Boolean).join(' ')

/**
 * Botón estándar del sistema. `variante`: primario (acción principal) o secundario.
 * `type` es "button" por defecto: un botón no envía el formulario salvo que se indique type="submit".
 */
export default function Boton({ variante = 'primario', type = 'button', className = '', ...props }) {
  return <button type={type} className={claseBoton(variante, className)} {...props} />
}

/** Enlace con aspecto de botón estándar. */
export function BotonEnlace({ variante = 'primario', className = '', ...props }) {
  return <Link className={claseBoton(variante, className)} {...props} />
}
