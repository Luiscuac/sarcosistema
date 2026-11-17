import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import RayosXLayout from '../../components/RayosXLayout.jsx'
import { mensajeErrorApi, obtenerEstudio } from '../../api/radiologiaApi.js'
import { useVistaImagen } from '../components/GaleriaImagenes.jsx'
import { partirTextoInforme } from '../utils/informe.js'
import '../../../laboratorio/pages/informe-solicitud.css'
import './estudio.css'

const nombresProyecciones = detalle => (detalle.adquisicion?.proyecciones_realizadas || []).map(c => detalle.config?.proyecciones?.find(p => p.codigo === c)?.nombre || c).join(', ') || 'No registradas'
function AnexoImagen({ imagen, detalle, indice }) {
  const url = useVistaImagen(imagen.archivo_id); const proyeccion = detalle.config?.proyecciones?.find(p => p.codigo === imagen.proyeccion_codigo)?.nombre || imagen.proyeccion_codigo || 'Sin asignar'
  return <section className="rxe-anexo-pagina"><h2>Anexo de imagenes · {indice + 1}</h2>{url ? <img src={url} alt={imagen.nombre_original} /> : <p>Cargando imagen...</p>}<p>{proyeccion} · {imagen.nombre_original}</p></section>
}

export function DocumentoInformeRx({ detalle, incluirImagenes }) {
  const { estudio, paciente, solicitud, adquisicion, informe, adendas = [] } = detalle
  const borrador = informe?.estado !== 'publicado'
  return <><article className="lab-report-document rxe-documento">
    {borrador && <p className="rxe-marca-borrador">BORRADOR — sin validez diagnostica</p>}
    <header className="lab-report-header"><div><p className="lab-report-institution">SarcoSistema · Rayos X</p><h1>Informe radiologico</h1></div><strong>{estudio.referencia_estudio}<br />{solicitud.referencia}</strong></header>
    <dl className="lab-report-meta"><div className="is-wide"><dt>Paciente</dt><dd>{paciente.nombre_completo}</dd></div><div><dt>Documento</dt><dd>{paciente.numero_documento || '—'}</dd></div><div><dt>Edad / sexo</dt><dd>{paciente.edad ?? '—'} / {paciente.sexo || '—'}</dd></div><div><dt>Fecha del examen</dt><dd>{adquisicion?.fecha_hora_adquisicion ? new Date(adquisicion.fecha_hora_adquisicion).toLocaleString('es-BO') : 'No registrada'}</dd></div><div className="is-wide"><dt>Medico solicitante</dt><dd>{solicitud.medico_solicitante || '—'}</dd></div></dl>
    <section className="rxe-datos-impresos"><h2>Datos del estudio</h2><dl><div><dt>Examen</dt><dd>{estudio.tipo_estudio_nombre}</dd></div><div><dt>Region</dt><dd>{detalle.config?.region || '—'}</dd></div><div><dt>Lateralidad</dt><dd>{estudio.detalle?.lateralidad || 'No aplica'}</dd></div><div><dt>Proyecciones</dt><dd>{nombresProyecciones(detalle)}</dd></div><div><dt>Indicacion clinica</dt><dd>{estudio.detalle?.indicacion_clinica || '—'}</dd></div></dl></section>
    <section className="rxe-cuerpo-informe">{partirTextoInforme(informe?.texto || '').map((seccion, i) => <section key={`${seccion.titulo}-${i}`}>{seccion.titulo && <h2>{seccion.titulo}</h2>}<p>{seccion.lineas.join('\n')}</p></section>)}</section>
    {adendas.length > 0 && <section className="rxe-adendas-impresas"><h2>Adendas</h2>{adendas.map(a => <article key={a.id}><h3>{new Date(a.fecha_hora).toLocaleString('es-BO')} · {a.autor_nombre}</h3><strong>{a.motivo}</strong><p>{a.texto}</p></article>)}</section>}
    <footer className="lab-report-signature"><div><p>Profesional responsable: {informe?.responsable_nombre || 'No informado'}</p><p>Registro profesional: {informe?.registro_profesional || 'No informado'}</p><p>Validado: {informe?.fecha_hora_publicacion ? new Date(informe.fecha_hora_publicacion).toLocaleString('es-BO') : 'No validado'}</p><p>Identificador: {estudio.referencia_estudio} · version {informe?.numero_version || 1}</p></div><div className="lab-report-sign-line"><span /><p>Firma y sello</p></div></footer>
  </article>{incluirImagenes && (detalle.imagenes || []).map((imagen, i) => <AnexoImagen key={imagen.id} imagen={imagen} detalle={detalle} indice={i} />)}</>
}

export default function InformeImpresoRxPage({ usuario, logout }) {
  const { estudioId } = useParams(); const [incluir, setIncluir] = useState(false)
  const { data: detalle, isLoading, isError, error } = useQuery({ queryKey: ['radiologia', 'estudio', estudioId], queryFn: ({ signal }) => obtenerEstudio(estudioId, signal) })
  const navegacion = { volverA: `/rayos-x/gestion/estudios/${estudioId}?seccion=informe`, textoVolver: 'Volver al estudio', migas: [{ texto: 'Rayos X', ruta: '/rayos-x/gestion' }, { texto: detalle?.estudio?.referencia_estudio || 'Estudio', ruta: `/rayos-x/gestion/estudios/${estudioId}` }, { texto: 'Informe impreso' }] }
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacion}><div className="lab-report-controls rxe-controles-impresion"><label><input type="checkbox" checked={incluir} onChange={e => setIncluir(e.target.checked)} /> Incluir imagenes como anexo</label><button type="button" className="primary-button" disabled={!detalle} onClick={() => window.print()}>Imprimir o guardar PDF</button></div>
    {isLoading && <p>Cargando informe...</p>}{isError && <p role="alert" className="lab-report-error">{mensajeErrorApi(error, 'No se pudo cargar el informe.')}</p>}{detalle && <DocumentoInformeRx detalle={detalle} incluirImagenes={incluir} />}</RayosXLayout>
}
