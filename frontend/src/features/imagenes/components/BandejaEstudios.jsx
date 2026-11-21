import { useState } from 'react'
import { Link } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import '../../laboratorio/pages/laboratorio.css'
import { estadoEstudioImagen } from '../../consultas/utils/examenes.js'
import '../pages/imagenes.css'
import { avisoPatronTb, NIVELES_TRIAJE, nombreHallazgo, ordenarBandeja } from '../../rayos_x/analisis.js'

function InsigniaTriaje({ triaje }) {
  if (!triaje) return <span className="img-triaje es-sin">Sin análisis IA</span>
  if (triaje.estado === 'en_proceso') return <span className="img-triaje es-proceso" role="status">IA analizando…</span>
  if (triaje.estado === 'error' || triaje.indice == null) return <span className="img-triaje es-sin">IA no disponible</span>
  const nivel = NIVELES_TRIAJE[triaje.nivel] || NIVELES_TRIAJE.baja
  const motivos = (triaje.contribuciones || []).map(c => nombreHallazgo(c.name)).join(', ')
  const tb = avisoPatronTb(triaje.patron_tb, triaje.nivel)
  return <>
    <span className={`img-triaje es-${nivel.clase}`} title={motivos ? `Pesan más: ${motivos}` : undefined}>
      {nivel.texto} · {Math.round(triaje.indice * 100)}{triaje.calidad === 'revisar' ? ' · revisar calidad' : ''}
    </span>
    {tb && <span className={`img-triaje-tb es-${tb.clave}`} title={`${tb.titulo}. ${tb.texto} Señal experimental.`}>{tb.corto}</span>}
  </>
}

export default function BandejaEstudios({ usuario, logout, modalidad = 'ecografia', bandeja, accion }) {
  const rayosX = modalidad === 'rayos_x'
  const titulo = rayosX ? 'Rayos X' : 'Ecografía'
  const rutaBandeja = rayosX ? '/rayos-x/gestion' : '/ecografia'
  const [vista, setVista] = useState('pendientes')
  const [busqueda, setBusqueda] = useState('')
  const [tipo, setTipo] = useState('todos')
  const [orden, setOrden] = useState('prioridad')
  const estudios = (bandeja.data || []).filter(e => rayosX
    ? /radiograf|rayos x/i.test(e.tipo_estudio_nombre)
    : /ecograf/i.test(e.tipo_estudio_nombre))
  const pendientes = estudios.filter(e => e.estado === 'pendiente_muestra')
  const preparacion = estudios.filter(e => e.estado === 'resultado_en_preparacion')
  const finalizados = estudios.filter(e => e.estado === 'publicado')
  const filtrados = estudios.filter(e => {
    const coincideVista = vista === 'todos' || (vista === 'pendientes' && e.estado === 'pendiente_muestra') || (vista === 'preparacion' && e.estado === 'resultado_en_preparacion') || (vista === 'finalizados' && e.estado === 'publicado')
    const texto = `${e.paciente_nombre} ${e.referencia_estudio} ${e.referencia_solicitud}`.toLocaleLowerCase()
    return coincideVista && texto.includes(busqueda.trim().toLocaleLowerCase()) && (tipo === 'todos' || e.tipo_estudio_nombre === tipo)
  })
  const visibles = rayosX ? ordenarBandeja(filtrados, orden) : filtrados
  const tipos = [...new Set(estudios.map(e => e.tipo_estudio_nombre))].sort()

  return <main className={`lab-page img-page${rayosX ? '' : ' eco-image-page'}`}>
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo={titulo} inicio={rutaBandeja} onLogout={logout} />
      <section className="lab-content">
        <div className="lab-title-row"><div><p className="lab-eyebrow">{rayosX ? 'RAYOS X' : 'ECOGRAFÍAS'}</p><h1>Bandeja de estudios</h1><p className="lab-intro">Consulta cada estudio y prepara o revisa su informe.</p></div><div className="lab-title-actions">{accion}</div></div>
        <section className="lab-list-panel" aria-label={`Estudios de ${titulo}`}>
          <div className="img-resumen" aria-label="Resumen de estudios">
            <button type="button" className={vista === 'pendientes' ? 'activo' : ''} onClick={() => setVista('pendientes')}><strong>{pendientes.length}</strong><span>Pendientes</span></button>
            <button type="button" className={vista === 'preparacion' ? 'activo' : ''} onClick={() => setVista('preparacion')}><strong>{preparacion.length}</strong><span>En preparación</span></button>
            <button type="button" className={vista === 'finalizados' ? 'activo' : ''} onClick={() => setVista('finalizados')}><strong>{finalizados.length}</strong><span>Finalizados</span></button>
          </div>
          <div className="img-filtros">
            <label>Buscar<input type="search" value={busqueda} onChange={e => setBusqueda(e.target.value)} placeholder="Paciente o referencia" /></label>
            <label>Tipo de estudio<select value={tipo} onChange={e => setTipo(e.target.value)}><option value="todos">Todos</option>{tipos.map(t => <option key={t} value={t}>{t}</option>)}</select></label>
            <label>Vista<select value={vista} onChange={e => setVista(e.target.value)}><option value="pendientes">Pendientes</option><option value="preparacion">En preparación</option><option value="finalizados">Finalizados</option><option value="todos">Todos los estados</option></select></label>
            {rayosX && <label>Ordenar<select value={orden} onChange={e => setOrden(e.target.value)}><option value="prioridad">Prioridad (urgentes e IA)</option><option value="llegada">Llegada (urgentes primero)</option></select></label>}
          </div>
          {rayosX && <p className="img-aviso-ia">La prioridad IA ordena la revisión según la radiografía; no es diagnóstico y sus umbrales son provisionales hasta calibrarlos con casos del hospital.</p>}
          {bandeja.isPending && <p role="status" className="img-mensaje">Cargando bandeja…</p>}
          {bandeja.isError && <p role="alert" className="img-mensaje">No se pudo cargar la bandeja.</p>}
          {bandeja.data && filtrados.length === 0 && <p className="img-mensaje">No hay estudios que coincidan con estos filtros.</p>}
          {visibles.length > 0 && (rayosX
            ? <div className="img-tarjetas">
              {visibles.map(estudio => <article className={`img-tarjeta${estudio.triaje?.nivel === 'alta' ? ' es-prioritaria' : ''}`} key={estudio.estudio_id}>
                <div className="img-tarjeta-cabecera"><div><p>{estudio.referencia_estudio}</p><h2>{estudio.tipo_estudio_nombre}</h2></div><span className={`lab-status lab-status--${estudio.estado}`}>{estadoEstudioImagen(estudio.estado)}</span></div>
                {(estudio.prioridad === 'urgente' || rayosX) && <div className="img-insignias">{estudio.prioridad === 'urgente' && <span className="img-triaje es-urgente">Urgente</span>}{rayosX && <InsigniaTriaje triaje={estudio.triaje} />}</div>}
                <dl><div><dt>Paciente</dt><dd>{estudio.paciente_nombre}</dd></div><div><dt>Solicitud</dt><dd>{estudio.referencia_solicitud}</dd></div><div><dt>Fecha</dt><dd>{new Date(estudio.fecha_solicitud).toLocaleDateString('es-BO')}</dd></div></dl>
                <div className="img-tarjeta-acciones"><Link className="lab-secondary-button" to={`${rutaBandeja}/estudios/${estudio.estudio_id}/informe`}>Ver informe</Link></div>
              </article>)}
            </div>
            : <div className="eco-study-list">
              {visibles.map(estudio => <article className="eco-study-row" key={estudio.estudio_id}>
                <div className="eco-study-name">
                  <span>Referencia · {estudio.referencia_estudio}</span>
                  <strong>{estudio.tipo_estudio_nombre}</strong>
                </div>
                <div className="eco-study-patient">
                  <span>Paciente</span>
                  <strong>{estudio.paciente_nombre}</strong>
                </div>
                <div className="eco-study-request">
                  <span>Solicitud · {estudio.referencia_solicitud}</span>
                  <span>Fecha · {new Date(estudio.fecha_solicitud).toLocaleDateString('es-BO')}</span>
                </div>
                <span className={`eco-study-status eco-study-status--${estudio.estado}`}><span aria-hidden="true" />{estadoEstudioImagen(estudio.estado)}</span>
                <Link className="eco-study-open" to={`${rutaBandeja}/estudios/${estudio.estudio_id}/informe`}>Abrir estudio <span aria-hidden="true">→</span></Link>
              </article>)}
            </div>)}
        </section>
      </section>
    </div>
  </main>
}
