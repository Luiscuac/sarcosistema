import { agruparPorCategoria, estadoSolicitud } from '../../utils/agruparSolicitudes.js'
import './solicitudes-panel.css'

function AccionEstudio({ estudio, vista, onAbrirResultado }) {
  if (vista === 'publicados') return <button type="button" onClick={() => onAbrirResultado(estudio)}>Ver resultado</button>
  if (estudio.estado === 'pendiente_muestra') return null
  return <button type="button" onClick={() => onAbrirResultado(estudio)}>Capturar resultado</button>
}

export default function SolicitudRow({ solicitud, abierta, vista, onToggle, onRecibirMuestra, onAbrirResultado }) {
  const pendientesMuestra = solicitud.estudios.filter((estudio) => estudio.estado === 'pendiente_muestra')

  return <>
    <tr className="lab-table-row">
      <td><strong>{solicitud.referencia}</strong><span>{solicitud.paciente_nombre}</span><small>{new Date(solicitud.fecha_solicitud).toLocaleString()}</small></td>
      <td><span className="lab-status">{estadoSolicitud(solicitud.estudios)}</span></td>
      <td>{solicitud.estudios.length} {solicitud.estudios.length === 1 ? 'estudio' : 'estudios'}</td>
      <td>{solicitud.prioridad === 'urgente' ? <strong className="lab-priority">Urgente</strong> : 'Normal'}</td>
      <td className="lab-row-action"><button type="button" aria-expanded={abierta} aria-controls={`solicitud-${solicitud.id}`} onClick={onToggle}>{abierta ? 'Ocultar estudios' : 'Abrir solicitud'}</button></td>
    </tr>
    {abierta && <tr className="lab-request-detail-row"><td colSpan="5">
      <div className="lab-request-detail" id={`solicitud-${solicitud.id}`}>
        {vista === 'pendientes' && pendientesMuestra.length > 0 && <div className="lab-sample-action">
          <div><strong>Muestras de la solicitud</strong><p>Registra la muestra y selecciona los estudios que se harán con ella. Si requieren muestras distintas, regístralas por separado.</p></div>
          <button type="button" onClick={() => onRecibirMuestra(solicitud)}>Registrar muestra</button>
        </div>}
        {agruparPorCategoria(solicitud.estudios).map((categoria) => <section key={categoria.codigo ?? 'otros'}>
          <h3>{categoria.nombre}</h3>
          <div className="lab-request-studies">
            {categoria.estudios.map((estudio) => <div className="lab-request-study" key={estudio.estudio_id}>
              <div><strong>{estudio.tipo_estudio_nombre}</strong><span>{estudio.estado === 'pendiente_muestra' ? 'Pendiente de muestra' : estudio.estado === 'publicado' ? 'Publicado' : 'En preparación'}</span></div>
              <AccionEstudio estudio={estudio} vista={vista} onAbrirResultado={onAbrirResultado} />
            </div>)}
          </div>
        </section>)}
      </div>
    </td></tr>}
  </>
}
