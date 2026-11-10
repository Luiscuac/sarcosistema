import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import '../pages/enfermeria.css'

export default function RecetaFicha({ receta, paciente, estado = 'Emitida' }) {
  const fechaEmision = receta.publicado_en
    ? new Date(receta.publicado_en).toLocaleString('es-BO')
    : formatearFecha(receta.fecha)
  const prescriptor = receta.prescriptor || receta.registrado_por || 'No indicado'
  return <article className="enf-panel enf-prescription-card">
    <header className="enf-prescription-heading">
      <div><span className="enf-prescription-kicker">RECETA MÉDICA</span><h2>{receta.numero_receta || `Receta #${receta.id}`}</h2></div>
      <span className="enf-prescription-status">{estado}</span>
    </header>
    <dl className="enf-prescription-meta">
      {paciente && <div><dt>Paciente</dt><dd>{paciente}</dd></div>}
      <div><dt>Historia clínica</dt><dd>{receta.historia_clinica || 'No registrada'}</dd></div>
      <div><dt>Médico prescriptor</dt><dd>{prescriptor}</dd></div>
      <div><dt>Fecha de emisión</dt><dd>{fechaEmision}</dd></div>
    </dl>
    <div className="enf-prescription-diagnosis"><span>Diagnóstico</span><p>{receta.diagnostico_principal || 'No indicado'}</p></div>
    <div className="enf-prescription-meds">
      <h3>Medicamentos prescritos <span>{receta.medicamentos?.length || 0}</span></h3>
      {receta.medicamentos?.map((medicamento, indice) => <section className="enf-prescription-med" key={`${receta.id}-${indice}`}>
        <div><strong>{medicamento.nombre_generico}</strong><span>{medicamento.forma_concentracion}</span></div>
        <p>{medicamento.indicaciones}</p>
        <footer><span>Cantidad prescrita</span><strong>{medicamento.cantidad_recetada || 'No especificada'}</strong></footer>
      </section>)}
    </div>
  </article>
}
