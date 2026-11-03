import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { obtenerInformeSolicitud } from '../api/laboratorioApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import './laboratorio.css'
import './informe-solicitud.css'

const categorias = {
  hematologia: 'Hematología',
  bioquimica: 'Bioquímica',
  serologia: 'Serología',
  copro_orina: 'Copro y orina',
}

const motivosIncidencia = {
  muestra_no_entregada: 'Muestra no entregada',
  toma_rechazada: 'Toma rechazada',
  toma_no_realizada: 'Toma no realizada',
}

function fechaVisible(valor) {
  return new Date(valor).toLocaleDateString('es-BO')
}

function seccionesDe(parametros) {
  const secciones = new Map()
  for (const parametro of parametros) {
    const nombre = parametro.seccion || 'Resultados'
    if (!secciones.has(nombre)) secciones.set(nombre, [])
    secciones.get(nombre).push(parametro)
  }
  return [...secciones]
}

export default function InformeSolicitudPage({ usuario, logout }) {
  const { solicitudId } = useParams()
  const { data: informe, isLoading, isError, error } = useQuery({
    queryKey: ['laboratorio', 'informe', solicitudId],
    queryFn: () => obtenerInformeSolicitud(solicitudId),
  })
  const categoriasConObservaciones = new Set()
  const ultimoEstudioPorCategoria = new Map()
  const responsablesPorCategoria = new Map()
  informe?.resultados.forEach((resultado) => {
    ultimoEstudioPorCategoria.set(resultado.categoria, resultado.referencia)
    if (resultado.responsable_publicacion) {
      const responsables = responsablesPorCategoria.get(resultado.categoria) ?? new Set()
      responsables.add(resultado.responsable_publicacion)
      responsablesPorCategoria.set(resultado.categoria, responsables)
    }
  })

  return <main className="lab-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} onLogout={logout} />
      <section className="lab-content lab-report-page">
        <div className="lab-report-controls">
          <Link className="lab-back-link" to={`/laboratorio/solicitudes/${solicitudId}`}>← Volver a la solicitud</Link>
          {informe && <button className="primary-button" type="button" onClick={() => window.print()}>Imprimir o guardar PDF</button>}
        </div>
        {isLoading && <p>Cargando informe…</p>}
        {isError && <p role="alert" className="lab-report-error">{error?.response?.status === 409
          ? 'El informe final estará disponible cuando todos los estudios estén publicados o cerrados como no realizados.'
          : error?.response?.status === 404 ? 'La solicitud no existe.' : 'No se pudo cargar el informe.'}</p>}
        {informe && <article className="lab-report-document">
          <header className="lab-report-header">
            <div><p className="lab-report-institution">SarcoSistema · Laboratorio</p><h1>Informe de resultados de laboratorio</h1></div>
            <strong>{informe.referencia}</strong>
          </header>
          <dl className="lab-report-meta">
            <div><dt>Paciente</dt><dd>{informe.paciente_nombre}</dd></div>
            <div><dt>Documento</dt><dd>{informe.paciente_documento || 'No registrado'}</dd></div>
            <div><dt>Fecha de solicitud</dt><dd>{fechaVisible(informe.fecha_solicitud)}</dd></div>
            <div><dt>N.º de formulario D-8</dt><dd>{informe.referencia_papel_formulario || 'No registrado'}</dd></div>
            <div><dt>Procedencia</dt><dd>{informe.procedencia === 'otro_centro' ? informe.establecimiento_solicitante_nombre : 'Sarcobamba'}</dd></div>
            <div><dt>Profesional solicitante</dt><dd>{informe.medico_solicitante_nombre || 'No registrado'}</dd></div>
          </dl>
          {informe.resultados.map((resultado) => {
            const mostrarObservaciones = Boolean(resultado.observaciones) && !categoriasConObservaciones.has(resultado.categoria)
            if (mostrarObservaciones) categoriasConObservaciones.add(resultado.categoria)
            return <section className="lab-report-study" key={resultado.referencia}>
            <div className="lab-report-study-title"><div><span>{categorias[resultado.categoria] || resultado.categoria || 'Laboratorio'}</span><h2>{resultado.nombre}</h2></div><small>{resultado.referencia}</small></div>
            {resultado.parametros.length === 0 && <p className="lab-report-empty">Sin parámetros informados.</p>}
            {seccionesDe(resultado.parametros).map(([seccion, parametros]) => {
              const tieneUnidad = parametros.some((parametro) => parametro.unidad)
              const tieneReferencia = parametros.some((parametro) => parametro.rango_referencia)
              return <div className="lab-report-section" key={seccion}>
                <h3>{seccion}</h3>
                <table><thead><tr><th scope="col">Parámetro</th><th scope="col">Resultado</th>{tieneUnidad && <th scope="col">Unidad</th>}{tieneReferencia && <th scope="col">Referencia</th>}</tr></thead>
                  <tbody>{parametros.map((parametro, index) => <tr key={`${seccion}-${index}`}><th scope="row">{parametro.nombre}</th><td>{parametro.valor}</td>{tieneUnidad && <td>{parametro.unidad || '—'}</td>}{tieneReferencia && <td>{parametro.rango_referencia || '—'}</td>}</tr>)}</tbody>
                </table>
              </div>
            })}
            {mostrarObservaciones && <p className="lab-report-observation"><strong>Observaciones de {categorias[resultado.categoria] || resultado.categoria || 'Laboratorio'}:</strong> {resultado.observaciones}</p>}
            {ultimoEstudioPorCategoria.get(resultado.categoria) === resultado.referencia && <p className="lab-report-responsible">Autorizó y publicó {categorias[resultado.categoria] || resultado.categoria || 'Laboratorio'}: {[...(responsablesPorCategoria.get(resultado.categoria) ?? [])].join(', ') || 'No registrado'}</p>}
          </section>
          })}
          {informe.estudios_no_realizados?.length > 0 && <section className="lab-report-not-performed">
            <h2>Estudios no realizados</h2>
            <p>Los siguientes estudios se cerraron sin resultado y conservan la justificación registrada por el laboratorio.</p>
            <table><thead><tr><th>Estudio</th><th>Motivo y detalle</th><th>Responsable</th><th>Fecha</th></tr></thead>
              <tbody>{informe.estudios_no_realizados.map((estudio) => <tr key={estudio.referencia}>
                <th scope="row"><span>{categorias[estudio.categoria] || estudio.categoria || 'Laboratorio'}</span>{estudio.nombre}</th>
                <td><strong>{motivosIncidencia[estudio.motivo] || estudio.motivo}</strong><br />{estudio.descripcion}</td>
                <td>{estudio.responsable}</td>
                <td>{new Date(estudio.fecha_hora).toLocaleString('es-BO')}</td>
              </tr>)}</tbody>
            </table>
          </section>}
        </article>}
      </section>
    </div>
  </main>
}
