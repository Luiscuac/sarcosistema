import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listarEstudios, mensajeErrorApi } from '../../api/radiologiaApi.js'
import RayosXLayout from '../../components/RayosXLayout.jsx'
import NuevaSolicitudRx from '../components/NuevaSolicitudRx.jsx'
import { agruparPorSolicitud, contarIndicadores, filtrarYOrdenarEstudios, INDICADORES_RX } from '../utils/bandejaRx.js'
import '../gestion.css'

const ACTUALIZACION_MS = 45_000
const ETAPAS = [
  ['pendiente_realizacion', 'Pendiente de realización'], ['en_adquisicion', 'En adquisición'],
  ['pendiente_informe', 'Pendiente de informe'], ['borrador', 'En borrador'],
  ['validado', 'Validado'], ['entregado', 'Entregado'], ['no_realizado', 'No realizado'], ['anulado', 'Anulado'],
]
const LATERALIDAD = { derecha: 'Derecha', izquierda: 'Izquierda', bilateral: 'Bilateral' }

function categoriaVisible(codigo) {
  return codigo ? codigo.replaceAll('_', ' ').replace(/^./, (letra) => letra.toLocaleUpperCase()) : 'Sin categoría'
}

function fechaVisible(fecha) {
  if (!fecha) return 'Fecha no registrada'
  const valor = new Date(fecha)
  return Number.isNaN(valor.getTime()) ? 'Fecha no registrada' : valor.toLocaleString('es-BO', { dateStyle: 'medium', timeStyle: 'short' })
}

function GrupoSolicitud({ solicitud }) {
  return <article className={solicitud.prioridad === 'urgente' ? 'rxg-solicitud is-urgent' : 'rxg-solicitud'}>
    <header className="rxg-solicitud-cabecera">
      <div>
        <Link to={`/rayos-x/gestion/solicitudes/${solicitud.id}`}>{solicitud.referencia}</Link>
        <h3>{solicitud.paciente_nombre}</h3>
        <p>{solicitud.paciente_documento ? `Documento ${solicitud.paciente_documento}` : 'Sin documento'} · {fechaVisible(solicitud.fecha_solicitud)}</p>
      </div>
      <dl>
        <div><dt>Prioridad</dt><dd>{solicitud.prioridad === 'urgente' ? 'Urgente' : 'Sin prioridad'}</dd></div>
        <div><dt>Médico</dt><dd>{solicitud.medico_solicitante || 'No registrado'}</dd></div>
      </dl>
    </header>
    <div className="rxg-estudios-lista">{solicitud.estudios.map((estudio) => <div className="rxg-estudio-fila" key={estudio.estudio_id}>
      <div className="rxg-estudio-identidad"><strong>{estudio.tipo_estudio_nombre}</strong><span>{LATERALIDAD[estudio.lateralidad] ?? 'Sin lateralidad'} · {estudio.imagenes ?? 0} {(estudio.imagenes ?? 0) === 1 ? 'imagen' : 'imagenes'}</span></div>
      <div className="rxg-insignias"><span className={`rxg-etapa rxg-etapa--${estudio.etapa}`}>{estudio.etapa_texto}</span>{estudio.triaje && <span className={`rxg-triaje rxg-triaje--${estudio.triaje.nivel ?? 'neutro'}`}>Prioridad IA: {estudio.triaje.nivel ?? 'sin nivel'}</span>}</div>
      <Link className="lab-secondary-button rxg-abrir" to={`/rayos-x/gestion/estudios/${estudio.estudio_id}`}>Abrir estudio</Link>
    </div>)}</div>
  </article>
}

export default function PanelRayosXPage({ usuario, logout }) {
  const indicadorInicial = usuario?.rol === 'radiologo' ? 'pendiente_informe' : 'pendiente_realizacion'
  const [vista, setVista] = useState('activos')
  const [indicador, setIndicador] = useState(indicadorInicial)
  const [busqueda, setBusqueda] = useState('')
  const [categoria, setCategoria] = useState('')
  const [etapa, setEtapa] = useState('')
  const [mostrarNueva, setMostrarNueva] = useState(false)
  const [creada, setCreada] = useState(null)
  const activosQuery = useQuery({ queryKey: ['radiologia', 'estudios', 'activos'], queryFn: ({ signal }) => listarEstudios('activos', signal), refetchInterval: ACTUALIZACION_MS })
  const finalizadosQuery = useQuery({ queryKey: ['radiologia', 'estudios', 'finalizados'], queryFn: ({ signal }) => listarEstudios('finalizados', signal), enabled: vista === 'finalizados', refetchInterval: ACTUALIZACION_MS })
  const consulta = vista === 'activos' ? activosQuery : finalizadosQuery
  const conteos = contarIndicadores(activosQuery.data ?? [])
  const categorias = [...new Set((consulta.data ?? []).map((estudio) => estudio.categoria).filter(Boolean))].sort()
  const visibles = useMemo(() => filtrarYOrdenarEstudios(consulta.data ?? [], {
    busqueda, categoria, etapa, indicador: vista === 'activos' ? indicador : '',
  }), [consulta.data, busqueda, categoria, etapa, indicador, vista])
  const solicitudes = agruparPorSolicitud(visibles)
  const hayFiltros = Boolean(busqueda.trim() || categoria || etapa || (vista === 'activos' && indicador))
  const listaBaseVacia = (consulta.data ?? []).length === 0

  function cambiarVista(nuevaVista) {
    setVista(nuevaVista)
    setIndicador(nuevaVista === 'activos' ? indicadorInicial : '')
    setCategoria('')
    setEtapa('')
  }

  return <RayosXLayout usuario={usuario} logout={logout}>
    <div className="lab-title-row">
      <div><p className="lab-eyebrow">RAYOS X</p><h1>Estudios de Rayos X</h1></div>
      {usuario?.rol === 'rayos_x' && <div className="lab-title-actions"><button className="primary-button" type="button" onClick={() => { setCreada(null); setMostrarNueva(true) }}>Nueva solicitud</button></div>}
    </div>
    {creada && <div className="lab-created-notice" role="status"><span>Solicitud <strong>{creada.referencia}</strong> registrada.</span><Link className="primary-button" to={`/rayos-x/gestion/solicitudes/${creada.solicitud_id}`}>Ver solicitud</Link><button type="button" aria-label="Cerrar aviso" onClick={() => setCreada(null)}>×</button></div>}

    <div className="lab-summary rxg-resumen" aria-label="Indicadores de Rayos X">{INDICADORES_RX.map((item) => {
      const activo = vista === 'activos' && indicador === item.codigo
      return <button type="button" key={item.codigo} aria-pressed={activo} className={activo ? 'lab-summary-card is-active' : 'lab-summary-card'} onClick={() => { setVista('activos'); setIndicador(activo ? '' : item.codigo) }}>
        <strong>{activosQuery.isLoading ? '…' : activosQuery.isError ? '—' : conteos[item.codigo]}</strong><span>{item.nombre}</span>{activosQuery.isError && <small>No disponible</small>}
      </button>
    })}</div>

    <section className="lab-list-panel rxg-panel">
      <div className="lab-list-toolbar"><h2>{vista === 'activos' ? 'Estudios en curso' : 'Estudios finalizados'}</h2><span className="lab-pending-tag">{consulta.isFetching && !consulta.isLoading ? 'Actualizando...' : 'Se actualiza cada 45 segundos'}</span></div>
      <div className="lab-list-tabs" role="tablist" aria-label="Vista de estudios"><button type="button" role="tab" aria-selected={vista === 'activos'} className={vista === 'activos' ? 'is-active' : ''} onClick={() => cambiarVista('activos')}>En curso</button><button type="button" role="tab" aria-selected={vista === 'finalizados'} className={vista === 'finalizados' ? 'is-active' : ''} onClick={() => cambiarVista('finalizados')}>Finalizados</button></div>
      <div className="rxg-filtros">
        <label>Buscar<input type="search" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Paciente, documento o referencia" /></label>
        <label>Categoría anatómica<select value={categoria} onChange={(e) => setCategoria(e.target.value)}><option value="">Todas</option>{categorias.map((codigo) => <option key={codigo} value={codigo}>{categoriaVisible(codigo)}</option>)}</select></label>
        <label>Etapa<select value={etapa} onChange={(e) => setEtapa(e.target.value)}><option value="">Todas</option>{ETAPAS.map(([codigo, nombre]) => <option key={codigo} value={codigo}>{nombre}</option>)}</select></label>
      </div>
      {consulta.isLoading && <div className="rxg-estado"><strong>Cargando estudios...</strong><span>La bandeja estará disponible en un momento.</span></div>}
      {consulta.isError && <div className="rxg-estado" role="alert"><strong>No se pudo cargar la bandeja.</strong><span>{mensajeErrorApi(consulta.error, 'Comprueba la conexión e intenta nuevamente.')}</span></div>}
      {consulta.isSuccess && solicitudes.length === 0 && <div className="rxg-estado"><strong>{!listaBaseVacia && hayFiltros ? 'No hay estudios con esos filtros.' : vista === 'activos' ? 'No hay estudios en curso.' : 'Todavía no hay estudios finalizados.'}</strong><span>{!listaBaseVacia && hayFiltros ? 'Prueba otra búsqueda o quita los filtros activos.' : vista === 'activos' ? usuario?.rol === 'rayos_x' ? 'Registra una nueva solicitud para iniciar el recorrido.' : 'Los estudios aparecerán cuando el personal técnico complete la adquisición.' : 'Los estudios aparecerán aquí cuando concluyan su recorrido.'}</span></div>}
      {consulta.isSuccess && solicitudes.length > 0 && <div className="rxg-solicitudes">{solicitudes.map((solicitud) => <GrupoSolicitud key={solicitud.id} solicitud={solicitud} />)}</div>}
    </section>
    {mostrarNueva && <NuevaSolicitudRx onClose={() => setMostrarNueva(false)} onCreated={setCreada} />}
  </RayosXLayout>
}
