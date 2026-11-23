import Dialogo from '../../../../shared/ui/Dialogo.jsx'
import InformeEcografiaDocumento from '../InformeEcografiaDocumento.jsx'

/** "Revisar y publicar": el documento tal como lo verá el médico, antes de confirmar (como en Laboratorio). */
export default function ConfirmarPublicacionEco({ estudio, datos, guardados, pendiente, onConfirmar, onCancelar }) {
  return <Dialogo eyebrow="REVISAR Y PUBLICAR" titulo={`${estudio.tipo_estudio_nombre} · ${estudio.paciente_nombre}`} onCerrar={onCancelar} bloqueado={pendiente}
    descripcion="Revisa el informe. Al publicarlo, el médico podrá consultarlo en la ficha del paciente y ya no se podrá editar.">
    <div className="lab-dialog-body eco-previa">
      <InformeEcografiaDocumento estudio={estudio} datos={datos} guardados={guardados} archivos={[]} publicado={false} />
    </div>
    <footer className="lab-dialog-footer">
      <p className="lab-dialog-summary">{guardados.length} {guardados.length === 1 ? 'adjunto' : 'adjuntos'}</p>
      <button type="button" disabled={pendiente} onClick={onCancelar}>Seguir editando</button>
      <button type="button" className="primary-button" disabled={pendiente} onClick={onConfirmar}>{pendiente ? 'Publicando…' : 'Publicar informe'}</button>
    </footer>
  </Dialogo>
}
