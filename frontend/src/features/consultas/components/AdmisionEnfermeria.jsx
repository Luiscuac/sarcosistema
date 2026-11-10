import { formularioDesdeRegistro, resumenDelFormulario } from '../../enfermeria/utils/signosVitales.js'
import { esDeHoy } from '../utils/paciente.js'

const hora = (instante) => new Date(instante).toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })
const fechaHora = (instante) => new Date(instante).toLocaleString('es-BO', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })

/**
 * Última admisión publicada por enfermería, resumida, con la acción de copiarla a la consulta.
 * Reemplaza la lista completa de registros y recetas que alargaba la pantalla.
 */
export default function AdmisionEnfermeria({ consulta, transferencia, onUsar }) {
  if (consulta.isPending) return <p role="status" className="med-message">Buscando la admisión de enfermería…</p>
  if (consulta.isError) return <p role="alert" className="med-message">No se pudo consultar la admisión de enfermería. Puedes registrar los signos vitales manualmente.</p>
  const registro = consulta.data?.[0]
  if (!registro) return <p className="med-message med-nursing-empty">Enfermería no publicó una admisión para este paciente. Registra los signos vitales en la consulta.</p>

  const deHoy = esDeHoy(registro.publicado_en)
  const lineas = resumenDelFormulario(formularioDesdeRegistro(registro))
  return <section className={`med-panel med-nursing-intake${deHoy ? '' : ' is-old'}`} aria-label="Admisión de enfermería">
    <div className="med-panel-header">
      <div><h2>Admisión de enfermería</h2>
        <span>{deHoy ? `Publicada hoy a las ${hora(registro.publicado_en)}` : `Publicada el ${fechaHora(registro.publicado_en)} · no es de hoy`} · {registro.publicado_por || registro.registrado_por}</span></div>
      {transferencia
        ? <span className="med-nursing-applied">{transferencia.copiados.length
          ? `${transferencia.copiados.length} datos copiados a la consulta · editables`
          : 'Sin datos nuevos para copiar'}</span>
        : <button type="button" className="med-secondary-button" onClick={onUsar}>Usar en la consulta</button>}
    </div>
    <dl className="enf-summary">{lineas.map(({ campo, etiqueta, valor }) => <div key={campo}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
    {transferencia?.conservados.length > 0 && <p className="med-hint">Se mantuvo lo que ya habías escrito en {transferencia.conservados.length === 1 ? 'un campo' : `${transferencia.conservados.length} campos`}; la admisión de enfermería queda arriba como referencia.</p>}
    {!deHoy && !transferencia && <p className="med-hint">Es una admisión anterior: revisa si los valores siguen vigentes antes de usarlos.</p>}
  </section>
}
