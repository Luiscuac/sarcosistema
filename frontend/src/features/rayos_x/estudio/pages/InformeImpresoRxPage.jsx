import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import RayosXLayout from '../../compartido/RayosXLayout.jsx'
import { obtenerEstudio } from '../../compartido/api/radiologiaApi.js'
import { useVistaImagen } from '../components/GaleriaImagenes.jsx'
import { partirTextoInforme } from '../utils/informe.js'
import '../../../laboratorio/pages/informe-solicitud.css'
import '../../../ecografia/pages/ecografia.css'
import './estudio.css'
import Boton from '../../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../../shared/utils/mensajeError.js'

const LATERALIDADES = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }
const nombresProyecciones = detalle => (detalle.adquisicion?.proyecciones_realizadas || []).map(c => detalle.config?.proyecciones?.find(p => p.codigo === c)?.nombre || c).join(', ') || 'No registradas'
const SEXOS = { M: 'Masculino', F: 'Femenino', masculino: 'Masculino', femenino: 'Femenino' }
const fechaCorta = valor => valor ? new Date(valor).toLocaleDateString('es-BO') : 'No registrada'

function LaminaImagen({ imagen, detalle }) {
  const url = useVistaImagen(imagen.archivo_id)
  const proyeccion = detalle.config?.proyecciones?.find(p => p.codigo === imagen.proyeccion_codigo)?.nombre || imagen.proyeccion_codigo || 'Proyección sin asignar'
  return <figure className="rxe-lamina">{url ? <img src={url} alt={imagen.nombre_original} /> : <p>{url === false ? 'No se pudo cargar la imagen.' : 'Cargando imagen…'}</p>}<figcaption>{proyeccion}</figcaption></figure>
}

/** Documento de lectura e impresión con el mismo formato institucional que el informe de ecografía. */
export function DocumentoInformeRx({ detalle, incluirImagenes }) {
  const { estudio, paciente, solicitud, adquisicion, informe, adendas = [] } = detalle
  const borrador = informe?.estado !== 'publicado'
  const lateralidad = LATERALIDADES[estudio.detalle?.lateralidad]
  const secciones = partirTextoInforme(informe?.texto || '')
  const conclusion = secciones.find(sec => /CONCLUSI/i.test(sec.titulo || ''))
  const cuerpo = secciones.filter(sec => sec !== conclusion)
  return <article className="lab-report-document eco-documento rxe-documento">
    <header className="eco-cabecera"><div><strong>CENTRO DE SALUD INTEGRAL SARCOBAMBA</strong><p>COCHABAMBA · CERCADO</p></div><strong>SERVICIO DE RAYOS X</strong></header>
    {borrador && <p className="eco-borrador">BORRADOR · PENDIENTE DE VALIDACIÓN</p>}
    <dl className="eco-identidad">
      <div><dt>Nombre:</dt><dd>{paciente.nombre_completo}</dd></div>
      <div><dt>Registro:</dt><dd>{paciente.codigo_paciente || 'No registrado'}</dd></div>
      <div><dt>Fecha del estudio:</dt><dd>{fechaCorta(adquisicion?.fecha_hora_adquisicion || solicitud.fecha_solicitud)}</dd></div>
      <div><dt>Documento:</dt><dd>{paciente.numero_documento || 'No registrado'}</dd></div>
      <div><dt>Establecimiento solicitante:</dt><dd>{solicitud.establecimiento || 'C.S. Sarcobamba'}</dd></div>
      <div><dt>Médico solicitante:</dt><dd>{solicitud.medico_solicitante || 'No registrado'}</dd></div>
    </dl>
    <p>Edad: {paciente.edad != null ? `${paciente.edad} años` : 'No registrada'} · Sexo: {SEXOS[paciente.sexo] || paciente.sexo || 'No registrado'}</p>
    <h2 className="eco-titulo">{estudio.tipo_estudio_nombre}{lateralidad ? ` ${lateralidad.toLocaleLowerCase('es')}` : ''}</h2>
    <p className="eco-hallazgo"><strong>PROYECCIONES: </strong>{nombresProyecciones(detalle)}</p>
    {estudio.detalle?.indicacion_clinica && <p className="eco-hallazgo"><strong>INDICACIÓN CLÍNICA: </strong>{estudio.detalle.indicacion_clinica}</p>}
    {cuerpo.map((sec, i) => <p className="eco-hallazgo" key={`${sec.titulo}-${i}`}>{sec.titulo && <strong>{sec.titulo.replace(/:$/, '')}: </strong>}{sec.lineas.join('\n')}</p>)}
    <section className="eco-conclusion"><h3>CONCLUSIÓN</h3><p>{conclusion ? conclusion.lineas.join('\n') : 'Pendiente de registrar.'}</p></section>
    {adendas.length > 0 && <section className="eco-conclusion"><h3>ADENDAS</h3>{adendas.map(a => <p key={a.id}><strong>{new Date(a.fecha_hora).toLocaleDateString('es-BO')} · {a.motivo}: </strong>{a.texto}</p>)}</section>}
    <footer className="lab-report-signature"><div><span /><p>Firma y sello del profesional responsable</p><p>{informe?.responsable_nombre || ''}{informe?.registro_profesional ? ` · Reg. ${informe.registro_profesional}` : ''}</p></div><p>{estudio.referencia_estudio} · {borrador ? 'Borrador' : `Validado el ${fechaCorta(informe?.fecha_hora_publicacion)}`}</p></footer>
    {incluirImagenes && (detalle.imagenes || []).length > 0 && <section className="eco-laminas"><h3>IMÁGENES DEL ESTUDIO</h3><p>{paciente.nombre_completo} · {estudio.referencia_estudio}</p><div className="eco-galeria">{detalle.imagenes.map(imagen => <LaminaImagen key={imagen.id} imagen={imagen} detalle={detalle} />)}</div></section>}
  </article>
}

export default function InformeImpresoRxPage({ usuario, logout }) {
  const { estudioId } = useParams(); const [incluir, setIncluir] = useState(false)
  const { data: detalle, isLoading, isError, error } = useQuery({ queryKey: ['radiologia', 'estudio', estudioId], queryFn: ({ signal }) => obtenerEstudio(estudioId, signal) })
  const navegacion = { volverA: `/rayos-x/gestion/estudios/${estudioId}?seccion=informe`, textoVolver: 'Volver al estudio', migas: [{ texto: 'Rayos X', ruta: '/rayos-x/gestion' }, { texto: detalle?.estudio?.referencia_estudio || 'Estudio', ruta: `/rayos-x/gestion/estudios/${estudioId}` }, { texto: 'Informe impreso' }] }
  return <RayosXLayout usuario={usuario} logout={logout} navegacion={navegacion}><div className="lab-report-controls rxe-controles-impresión"><label><input type="checkbox" checked={incluir} onChange={e => setIncluir(e.target.checked)} /> Incluir imágenes como anexo</label><Boton disabled={!detalle} onClick={() => window.print()}>Imprimir o guardar PDF</Boton></div>
    {isLoading && <p>Cargando informe...</p>}{isError && <p role="alert" className="lab-report-error">{mensajeError(error, 'No se pudo cargar el informe.')}</p>}{detalle && <DocumentoInformeRx detalle={detalle} incluirImagenes={incluir} />}</RayosXLayout>
}
