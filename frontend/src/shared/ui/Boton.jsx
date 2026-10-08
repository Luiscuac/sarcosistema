export default function Boton({ children, onClick, variante = 'primario' }) {
  return (
    <button className={`boton boton--${variante}`} onClick={onClick}>
      {children}
    </button>
  )
}
