import { Link, useParams } from 'react-router-dom'
import MarcoEcografia, { migasEstudio } from '../components/MarcoEcografia.jsx'
import RecorridoEco from '../components/RecorridoEco.jsx'
import { useEstudioEcografia, usaPlantilla } from '../hooks/useEstudioEcografia.js'
import { accionPrincipalEco, iniciarDatos, resumenRegistro } from '../informe.js'
import { estadoEstudioImagen } from '../utils/archivos.js'
import { describirEdad } from '../../../shared/utils/edad.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import '../../laboratorio/pages/solicitud-detalle.css'

function DatosPedido({ estudio }) {
  const filas = [
    ['Paciente', estudio.paciente_nombre],
    ['Código del paciente', estudio.codigo_paciente || 'No registrado'],
    ['Historia clínica', estudio.historia_clinica || 'No registrada'],
    ['Edad actual', describirEdad(estudio.fecha_nacimiento) || 'No registrada'],
    ['Médico solicitante', estudio.medico_solicitante || 'No registrado'],
    ['Fecha de solicitud', formatearFecha(estudio.fecha_solicitud)],
    ['Referencia de la solicitud', estudio.referencia_solicitud],
    ['Referencia del estudio', estudio.referencia_estudio],
  ]
  return <section className="lab-detail-card">
    <h2>Datos del pedido</h2>
    <dl className="lab-detail-grid">{filas.map(([dt, dd]) => <div key={dt}><dt>{dt}</dt><dd>{dd}</dd></div>)}</dl>
  </section>
}

/** Detalle del estudio: dónde está, qué sigue y los datos del pedido (mismo esquema que una solicitud de Laboratorio). */
export default function EstudioEcografiaPage({ usuario, logout }) {
  const { estudioId } = useParams()
  const consulta = useEstudioEcografia(estudioId)
  const estudio = consulta.data
  const navegacion = { volverA: '/ecografia', textoVolver: 'Volver a la bandeja', migas: migasEstudio(estudio) }
  const accion = estudio && accionPrincipalEco(estudio)
  const plantilla = estudio && usaPlantilla(estudio)
  const avance = plantilla && estudio.informe && estudio.estado !== 'publicado'
    ? resumenRegistro(iniciarDatos(estudio), estudio.organos) : null

  return <MarcoEcografia usuario={usuario} logout={logout} navegacion={navegacion} clase="lab-detail-page">
    {consulta.isPending && <p role="status">Cargando estudio…</p>}
    {consulta.isError && <div role="alert" className="lab-detail-card"><h1>No se pudo cargar el estudio</h1><p>Vuelve a la bandeja e inténtalo de nuevo.</p></div>}
    {estudio && <>
      <div className="lab-title-row">
        <div>
          <p className="lab-eyebrow">ESTUDIO DE ECOGRAFÍA · {estudio.referencia_estudio}</p>
          <h1>{estudio.paciente_nombre}</h1>
          <p className="lab-intro">{estudio.tipo_estudio_nombre} · {estadoEstudioImagen(estudio.estado)}</p>
        </div>
        <div className="lab-title-actions"><Link className="primary-button lab-report-link" to={accion.ruta}>{accion.etiqueta}</Link></div>
      </div>

      <section className="lab-detail-card">
        <div className="lab-detail-heading">
          <div><h2>Recorrido del estudio</h2>
            <p>{estudio.estado === 'publicado' ? 'Informe publicado: el médico ya puede consultarlo en la ficha del paciente.'
              : estudio.informe ? 'Hay un borrador guardado. Continúa el registro y publícalo cuando esté completo.'
                : 'Aún no se registró el estudio.'}</p></div>
          <RecorridoEco estado={estudio.estado} />
        </div>
        {avance && <div className="lab-request-progress eco-avance">
          <span>{avance.completos} de {avance.total} campos del informe completos</span>
          <div className="lab-progress-bar" role="progressbar" aria-valuemin={0} aria-valuemax={avance.total} aria-valuenow={avance.completos} aria-label="Campos del informe completos">
            <span style={{ width: `${Math.round((avance.completos / avance.total) * 100)}%` }} />
          </div>
        </div>}
        {!plantilla && <p className="lab-form-hint">Este tipo de estudio usa el informe de texto libre.</p>}
      </section>

      {estudio.informe && <section className="lab-detail-card lab-report-access">
        <div><h2>{estudio.estado === 'publicado' ? 'Informe final' : 'Borrador del informe'}</h2>
          <p>{estudio.estado === 'publicado' ? 'Documento listo para imprimir o guardar en PDF.' : 'Vista del documento tal como se publicará.'}</p></div>
        <Link className={estudio.estado === 'publicado' ? 'primary-button lab-report-link' : 'lab-secondary-button'} to={`/ecografia/estudios/${estudio.estudio_id}/informe`}>
          {estudio.estado === 'publicado' ? 'Ver informe final' : 'Ver borrador'}</Link>
      </section>}

      <DatosPedido estudio={estudio} />
    </>}
  </MarcoEcografia>
}
