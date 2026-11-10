import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { obtenerInformeSolicitud } from '../api/laboratorioApi.js'
import { obtenerInformeLaboratorio } from '../../consultas/api/consultasApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NavegacionLab from '../components/NavegacionLab.jsx'
import { agruparPorSeccion } from '../utils/captura.js'
import { nombreArea, nombreMotivoIncidencia, nombreSexo } from '../utils/catalogos.js'
import { evaluarValor } from '../utils/rangoReferencia.js'
import { describirEdad } from '../../../shared/utils/edad.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import './laboratorio.css'
import './informe-solicitud.css'

/** Responsables por área y el último estudio de cada área (donde se imprime la firma). */
function resumenPorArea(resultados) {
  const ultimo = new Map()
  const responsables = new Map()
  for (const resultado of resultados) {
    ultimo.set(resultado.categoria, resultado.referencia)
    if (!resultado.responsable_publicacion) continue
    if (!responsables.has(resultado.categoria)) responsables.set(resultado.categoria, new Set())
    responsables.get(resultado.categoria).add(resultado.responsable_publicacion)
  }
  return { ultimo, responsables }
}

/** El informe no trae el tipo de entrada: solo se evalúan valores que son números. */
function fueraDeRango(parametro) {
  return /^\d[\d.,]*$/.test(String(parametro.valor).trim())
    && Boolean(evaluarValor(parametro.valor, parametro.rango_referencia, 'decimal'))
}

function TablaSeccion({ seccion, parametros }) {
  const tieneUnidad = parametros.some((parametro) => parametro.unidad)
  const tieneReferencia = parametros.some((parametro) => parametro.rango_referencia)
  return <div className="lab-report-section">
    <h3>{seccion}</h3>
    <table>
      <thead><tr><th scope="col">Parámetro</th><th scope="col">Resultado</th>{tieneUnidad && <th scope="col">Unidad</th>}{tieneReferencia && <th scope="col">Referencia</th>}</tr></thead>
      <tbody>{parametros.map((parametro, indice) => {
        const fuera = fueraDeRango(parametro)
        return <tr key={`${seccion}-${indice}`} className={fuera ? 'is-out-of-range' : undefined}>
          <th scope="row">{parametro.nombre}</th>
          <td>{parametro.valor}{fuera && <span className="sr-only"> (fuera del rango de referencia)</span>}</td>
          {tieneUnidad && <td>{parametro.unidad || '—'}</td>}
          {tieneReferencia && <td>{parametro.rango_referencia || '—'}</td>}
        </tr>
      })}</tbody>
    </table>
  </div>
}

function Informe({ informe }) {
  const { ultimo, responsables } = resumenPorArea(informe.resultados)
  const areasConObservaciones = new Set()
  const edad = describirEdad(informe.paciente_fecha_nacimiento)
  const hayFueraDeRango = informe.resultados.some((resultado) => resultado.parametros.some(fueraDeRango))

  return <article className="lab-report-document">
    <header className="lab-report-header">
      <div><p className="lab-report-institution">SarcoSistema · Laboratorio clínico</p><h1>Informe de resultados de laboratorio</h1></div>
      <strong>{informe.referencia}</strong>
    </header>
    <dl className="lab-report-meta">
      <div><dt>Paciente</dt><dd>{informe.paciente_nombre}</dd></div>
      <div><dt>Documento</dt><dd>{informe.paciente_documento || 'No registrado'}</dd></div>
      <div><dt>Edad</dt><dd>{edad || 'No registrada'}</dd></div>
      <div><dt>Sexo</dt><dd>{informe.paciente_sexo ? nombreSexo(informe.paciente_sexo) : 'No registrado'}</dd></div>
      <div><dt>Fecha de solicitud</dt><dd>{formatearFecha(informe.fecha_solicitud)}</dd></div>
      <div><dt>N.º de formulario D-8</dt><dd>{informe.referencia_papel_formulario || 'No registrado'}</dd></div>
      <div><dt>Procedencia</dt><dd>{informe.procedencia === 'otro_centro' ? informe.establecimiento_solicitante_nombre : 'Sarcobamba'}</dd></div>
      <div><dt>Profesional solicitante</dt><dd>{informe.medico_solicitante_nombre || 'No registrado'}</dd></div>
    </dl>
    {hayFueraDeRango && <p className="lab-report-legend">Los valores en <strong>rojo</strong> están fuera del rango de referencia impreso. La interpretación corresponde al profesional tratante.</p>}
    {informe.resultados.map((resultado) => {
      const area = nombreArea(resultado.categoria)
      const mostrarObservaciones = Boolean(resultado.observaciones) && !areasConObservaciones.has(resultado.categoria)
      if (mostrarObservaciones) areasConObservaciones.add(resultado.categoria)
      return <section className="lab-report-study" key={resultado.referencia}>
        <div className="lab-report-study-title"><div><span>{area}</span><h2>{resultado.nombre}</h2></div><small>{resultado.referencia}</small></div>
        {resultado.parametros.length === 0 && <p className="lab-report-empty">Sin parámetros informados.</p>}
        {agruparPorSeccion(resultado.parametros).map(([seccion, parametros]) => <TablaSeccion key={seccion} seccion={seccion} parametros={parametros} />)}
        {mostrarObservaciones && <p className="lab-report-observation"><strong>Observaciones de {area}:</strong> {resultado.observaciones}</p>}
        {ultimo.get(resultado.categoria) === resultado.referencia && <p className="lab-report-responsible">
          Autorizó y publicó {area}: {[...(responsables.get(resultado.categoria) ?? [])].join(', ') || 'No registrado'}
        </p>}
      </section>
    })}
    {informe.estudios_no_realizados?.length > 0 && <section className="lab-report-not-performed">
      <h2>Estudios no realizados</h2>
      <p>Los siguientes estudios se cerraron sin resultado y conservan la justificación registrada por el laboratorio.</p>
      <table><thead><tr><th>Estudio</th><th>Motivo y detalle</th><th>Responsable</th><th>Fecha</th></tr></thead>
        <tbody>{informe.estudios_no_realizados.map((estudio) => <tr key={estudio.referencia}>
          <th scope="row"><span>{nombreArea(estudio.categoria)}</span>{estudio.nombre}</th>
          <td><strong>{nombreMotivoIncidencia(estudio.motivo)}</strong><br />{estudio.descripcion}</td>
          <td>{estudio.responsable}</td>
          <td>{new Date(estudio.fecha_hora).toLocaleString('es-BO')}</td>
        </tr>)}</tbody>
      </table>
    </section>}
    <footer className="lab-report-signature">
      <div><span /><p>Firma y sello del responsable de laboratorio</p></div>
      <p>Emitido el {new Date().toLocaleString('es-BO')} · Documento generado por SarcoSistema</p>
    </footer>
  </article>
}

export default function InformeSolicitudPage({ usuario, logout, modoMedico = false, pacienteId }) {
  const { solicitudId } = useParams()
  const { data: informe, isLoading, isError, error } = useQuery({
    queryKey: ['laboratorio', 'informe', solicitudId, modoMedico],
    queryFn: () => (modoMedico ? obtenerInformeLaboratorio(solicitudId) : obtenerInformeSolicitud(solicitudId)),
  })

  const contenido = <>
    <div className="lab-report-controls">
      {modoMedico
        ? <Link className="lab-back-link" to={`/consultas/pacientes/${pacienteId}`}>← Volver a la ficha</Link>
        : <NavegacionLab volverA={`/laboratorio/solicitudes/${solicitudId}`} textoVolver="Volver a la solicitud" migas={[
          { texto: 'Solicitudes', ruta: '/laboratorio' },
          { texto: informe?.referencia ?? 'Solicitud', ruta: `/laboratorio/solicitudes/${solicitudId}` },
          { texto: 'Informe' },
        ]} />}
      {informe && <button className="primary-button" type="button" onClick={() => window.print()}>Imprimir o guardar PDF</button>}
    </div>
    {isLoading && <p>Cargando informe…</p>}
    {isError && <p role="alert" className="lab-report-error">{error?.response?.status === 409
      ? 'El informe final estará disponible cuando todos los estudios estén publicados o cerrados como no realizados.'
      : error?.response?.status === 404 ? 'El informe no está disponible.' : 'No se pudo cargar el informe.'}</p>}
    {informe && <Informe informe={informe} />}
  </>

  if (modoMedico) return <section className="lab-report-page">{contenido}</section>
  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-report-page">{contenido}</section>
    </div>
  </main>
}
