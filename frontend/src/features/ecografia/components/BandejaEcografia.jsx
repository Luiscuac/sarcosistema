import { useState } from 'react'
import { Link } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import { estadoEstudioImagen } from '../utils/archivos.js'
import { VISTAS, filtrarEstudios } from '../bandeja.js'
import '../../laboratorio/pages/laboratorio.css'

export default function BandejaEcografia({ usuario, logout, bandeja, onNueva, creada, onCerrarAviso }) {
  const [estado, setEstado] = useState('pendiente_muestra')
  const [buscar, setBuscar] = useState('')
  const [tipo, setTipo] = useState('todos')
  const estudios = bandeja.data || []
  const filtrados = filtrarEstudios(estudios, { estado, buscar, tipo })
  const tipos = [...new Set(estudios.map(e => e.tipo_estudio_nombre))].sort()
  const indicadores = [{ codigo: 'todos', nombre: 'Todos los estudios' }, ...VISTAS]
  const limpiar = () => { setBuscar(''); setTipo('todos'); setEstado('todos') }

  return <main className="lab-page eco-workspace"><LaboratorioTopbar usuario={usuario} titulo="Ecografía" inicio="/ecografia" onLogout={logout} />
    <section className="lab-content">
      <div className="lab-title-row"><div><p className="lab-eyebrow">SERVICIO DE ECOGRAFÍA</p><h1>Solicitudes de ecografía</h1><p className="lab-intro">De la solicitud al informe: registra los hallazgos, adjunta imágenes y publica el resultado.</p></div><div className="lab-title-actions"><button className="primary-button" type="button" onClick={onNueva}>+ Nueva solicitud</button></div></div>
      {creada && <div className="lab-created-notice" role="status"><span>Solicitud registrada para <strong>{creada.paciente}</strong> · {creada.cantidad} {creada.cantidad === 1 ? 'estudio' : 'estudios'}.</span><button type="button" onClick={onCerrarAviso} aria-label="Cerrar aviso">×</button></div>}
      <div className="lab-summary" aria-label="Indicadores de ecografía">{indicadores.map(i => <button type="button" key={i.codigo} aria-pressed={estado === i.codigo} className={`lab-summary-card${estado === i.codigo ? ' is-active' : ''}`} onClick={() => setEstado(i.codigo)}><strong>{bandeja.isPending ? '…' : bandeja.isError ? '—' : estudios.filter(e => i.codigo === 'todos' || e.estado === i.codigo).length}</strong><span>{i.nombre}</span></button>)}</div>
      <section className="lab-list-panel" aria-label="Bandeja de ecografía">
        <div className="lab-list-toolbar"><div><h2>Estudios solicitados</h2><p>Selecciona un estudio para comenzar o continuar su informe.</p></div><span className="eco-result-count">{filtrados.length} de {estudios.length} estudios</span></div>
        <div className="lab-list-tabs eco-list-tabs" aria-label="Filtrar por estado">{indicadores.map(i => <button type="button" className={estado === i.codigo ? 'is-active' : ''} aria-pressed={estado === i.codigo} key={i.codigo} onClick={() => setEstado(i.codigo)}>{i.codigo === 'todos' ? 'Todos' : i.nombre}</button>)}</div>
        <div className="eco-list-filters"><label>Buscar paciente, solicitud o estudio<input type="search" value={buscar} onChange={e => setBuscar(e.target.value)} placeholder="Nombre, referencia o tipo de ecografía" /></label><label>Tipo de ecografía<select value={tipo} onChange={e => setTipo(e.target.value)}><option value="todos">Todos los tipos</option>{tipos.map(t => <option key={t}>{t}</option>)}</select></label>{(buscar || tipo !== 'todos') && <button type="button" className="lab-secondary-button" onClick={limpiar}>Limpiar filtros</button>}</div>
        {bandeja.isPending ? <p className="img-mensaje" role="status">Cargando estudios…</p> : bandeja.isError ? <div className="lab-empty" role="alert"><strong>No se pudo cargar la bandeja.</strong><button type="button" className="lab-secondary-button" onClick={() => bandeja.refetch()}>Reintentar</button></div> : !filtrados.length ? <div className="lab-empty"><strong>{estudios.length ? 'No hay estudios con estos filtros' : 'Todavía no hay solicitudes de ecografía'}</strong><span>{estudios.length ? 'Prueba otro estado o limpia la búsqueda.' : 'Crea una solicitud para empezar a registrar el estudio.'}</span>{estudios.length > 0 && <button type="button" className="lab-secondary-button" onClick={limpiar}>Ver todos los estudios</button>}</div> : <div className="lab-table-wrap"><table className="lab-table eco-worklist"><thead><tr><th>Paciente / solicitud</th><th>Estudio</th><th>Fecha</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{filtrados.map(e => <tr className="lab-table-row" key={e.estudio_id}><td><strong>{e.paciente_nombre}</strong><small>{e.referencia_solicitud}</small></td><td><strong>{e.tipo_estudio_nombre}</strong><small>{e.referencia_estudio}</small>{e.prioridad === 'urgente' && <span className="eco-urgent">Urgente</span>}</td><td>{formatearFecha(e.fecha_solicitud)}</td><td><span className={`lab-status lab-status--${e.estado}`}>{estadoEstudioImagen(e.estado)}</span></td><td><Link className="lab-secondary-button" to={`/ecografia/estudios/${e.estudio_id}${e.estado === 'publicado' ? '/informe' : ''}`}>{VISTAS.find(v => v.codigo === e.estado)?.accion || 'Abrir estudio'} <span aria-hidden="true">→</span></Link></td></tr>)}</tbody></table></div>}
        <div className="eco-list-footer"><span>Los informes publicados están disponibles en la ficha médica del paciente.</span></div>
      </section>
    </section>
  </main>
}
