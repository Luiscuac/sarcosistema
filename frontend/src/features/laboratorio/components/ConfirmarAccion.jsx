import Dialogo from './Dialogo.jsx'

/** Confirmación explícita para acciones irreversibles o que descartan datos. */
export default function ConfirmarAccion({
  titulo, children, textoConfirmar, textoCancelar = 'Volver', peligro = false,
  pendiente = false, onConfirmar, onCancelar,
}) {
  return (
    <Dialogo compacto eyebrow="CONFIRMAR" titulo={titulo} onCerrar={onCancelar} bloqueado={pendiente}>
      <div className="lab-dialog-body lab-confirm-body">{children}</div>
      <footer className="lab-dialog-footer">
        <button type="button" onClick={onCancelar} disabled={pendiente} autoFocus>{textoCancelar}</button>
        <button type="button" className={peligro ? 'lab-incidence-submit' : 'primary-button'} onClick={onConfirmar} disabled={pendiente}>
          {pendiente ? 'Procesando…' : textoConfirmar}
        </button>
      </footer>
    </Dialogo>
  )
}
