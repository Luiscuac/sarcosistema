import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { obtenerInformeSolicitud } from '../api/laboratorioApi.js'
import { obtenerInformeLaboratorio } from '../../consultas/api/consultasApi.js'
import LaboratorioTopbar from '../components/LaboratorioTopbar.jsx'
import NavegacionLab from '../components/NavegacionLab.jsx'
import { nombreArea, nombreMotivoIncidencia, nombreSexo } from '../utils/catalogos.js'
import { agruparInformePorArea, fueraDeRango, resumenParaCopiar } from '../utils/informe.js'
import { describirEdad } from '../../../shared/utils/edad.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import './laboratorio.css'
import './informe-solicitud.css'

function FilaInforme({ fila, columnas }) {
  if (fila.tipo === 'estudio') return <tr className="lab-report-row-study"><th scope="rowgroup" colSpan={columnas}>{fila.nombre}</th></tr>
  if (fila.tipo === 'seccion') return <tr className="lab-report-row-section"><th scope="rowgroup" colSpan={columnas}>{fila.nombre}</th></tr>
  if (fila.tipo === 'vacio') return <tr><th scope="row">{fila.nombre}</th><td colSpan={columnas - 1} className="lab-report-empty">Sin parámetros informados</td></tr>
  const { parametro } = fila
  const fuera = fueraDeRango(parametro)
  const clases = [fuera && 'is-out-of-range', fila.enSeccion && 'is-indented'].filter(Boolean).join(' ')
  return <tr className={clases || undefined}>
    <th scope="row">{parametro.nombre}</th>
    <td>{parametro.valor}{fuera && <span className="sr-only"> (fuera del rango de referencia)</span>}</td>
    {columnas > 2 && <td>{parametro.unidad || ''}</td>}
    {columnas > 3 && <td>{parametro.rango_referencia || ''}</td>}
  </tr>
}

function TablaArea({ area }) {
  const nombre = nombreArea(area.categoria)
  // Unidad y referencia van juntas para que la columna de referencia no se corra.
  const columnas = area.tieneReferencia ? 4 : area.tieneUnidad ? 3 : 2
  return <section className="lab-report-area">
    <table>
      <caption>{nombre}</caption>
      <thead><tr><th scope="col">Estudio / parámetro</th><th scope="col">Resultado</th>{columnas > 2 && <th scope="col">Unidad</th>}{columnas > 3 && <th scope="col">Referencia</th>}</tr></thead>
      <tbody>{area.filas.map((fila, indice) => <FilaInforme key={indice} fila={fila} columnas={columnas} />)}</tbody>
    </table>
    {area.observaciones.length > 0 && <p className="lab-report-observation"><strong>Obs.:</strong> {area.observaciones.join(' · ')}</p>}
    <p className="lab-report-responsible">Autorizó y publicó {nombre}: {area.responsables.join(', ') || 'No registrado'}</p>
  </section>
}

async function copiarTexto(texto, campo) {
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    // Sin permiso de portapapeles: se selecciona el texto para copiarlo a mano.
    campo?.focus()
    campo?.select()
    return false
  }
}

function ResumenCopiable({ informe }) {
  const campo = useRef(null)
  const [estado, setEstado] = useState(null)
  const texto = resumenParaCopiar(informe, {
    nombreArea, nombreMotivo: nombreMotivoIncidencia, fecha: formatearFecha(informe.fecha_solicitud),
  })
  async function copiar() {
    setEstado(await copiarTexto(texto, campo.current) ? 'copiado' : 'manual')
  }
  return <section className="lab-report-copy" aria-labelledby="lab-report-copy-title">
    <div className="lab-report-copy-head">
      <div>
        <h2 id="lab-report-copy-title">Resumen para la nota clínica</h2>
        <p>Texto plano para pegar en el SOAP. No se imprime.</p>
      </div>
      <button className="lab-secondary-button" type="button" onClick={copiar}>{estado === 'copiado' ? 'Copiado ✓' : 'Copiar'}</button>
    </div>
    <textarea ref={campo} readOnly value={texto} rows={Math.min(8, texto.split('\n').length + 1)} onFocus={(evento) => evento.target.select()} />
    {estado === 'manual' && <p role="status" className="lab-report-copy-hint">No se pudo copiar automáticamente: el texto quedó seleccionado, usa Ctrl + C.</p>}
  </section>
}

function Informe({ informe }) {
  const areas = agruparInformePorArea(informe.resultados)
  const edad = describirEdad(informe.paciente_fecha_nacimiento)
  const sexo = informe.paciente_sexo ? nombreSexo(informe.paciente_sexo) : null
  const hayFueraDeRango = informe.resultados.some((resultado) => resultado.parametros.some(fueraDeRango))
  const procedencia = informe.procedencia === 'otro_centro' ? informe.establecimiento_solicitante_nombre : 'Sarcobamba'

  return <article className="lab-report-document is-compact">
    <header className="lab-report-header">
      <div><p className="lab-report-institution">SarcoSistema · Laboratorio clínico</p><h1>Informe de laboratorio</h1></div>
      <strong>{informe.referencia}</strong>
    </header>
    <dl className="lab-report-meta">
      <div className="is-wide"><dt>Paciente</dt><dd>{informe.paciente_nombre}</dd></div>
      <div><dt>Documento</dt><dd>{informe.paciente_documento || '—'}</dd></div>
      <div><dt>Edad / sexo</dt><dd>{[edad, sexo].filter(Boolean).join(' · ') || '—'}</dd></div>
      <div><dt>Solicitud</dt><dd>{formatearFecha(informe.fecha_solicitud)}</dd></div>
      <div className="is-wide"><dt>Solicitante</dt><dd>{informe.medico_solicitante_nombre || '—'}</dd></div>
      <div><dt>Procedencia</dt><dd>{procedencia}</dd></div>
      <div><dt>Form. D-8</dt><dd>{informe.referencia_papel_formulario || '—'}</dd></div>
    </dl>
    {hayFueraDeRango && <p className="lab-report-legend">Valores en <strong>rojo</strong>: fuera del rango de referencia.</p>}
    {areas.map((area) => <TablaArea key={area.categoria} area={area} />)}
    {informe.estudios_no_realizados?.length > 0 && <section className="lab-report-not-performed">
      <h2>No realizados</h2>
      <ul>{informe.estudios_no_realizados.map((estudio) => <li key={estudio.referencia}>
        <strong>{estudio.nombre}</strong> ({nombreArea(estudio.categoria)}): {nombreMotivoIncidencia(estudio.motivo)}
        {estudio.descripcion && <> — {estudio.descripcion}</>}
        <span> · {estudio.responsable}, {new Date(estudio.fecha_hora).toLocaleString('es-BO')}</span>
      </li>)}</ul>
    </section>}
    <footer className="lab-report-signature">
      <div>
        <p>Emitido el {new Date().toLocaleString('es-BO')} · SarcoSistema</p>
      </div>
      <div className="lab-report-sign-line"><span /><p>Firma y sello</p></div>
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
    {informe && <ResumenCopiable informe={informe} />}
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
