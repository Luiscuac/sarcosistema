import { useState } from 'react'
import { Link } from 'react-router-dom'
import LaboratorioTopbar from '../../laboratorio/components/LaboratorioTopbar.jsx'
import '../../laboratorio/pages/laboratorio.css'
import { estadoEstudioImagen } from '../../consultas/utils/examenes.js'
import '../pages/imagenes.css'

export default function BandejaEstudios({ usuario, logout, modalidad = 'ecografia', bandeja }) {
  const rayosX = modalidad === 'rayos_x'
  const titulo = rayosX ? 'Rayos X' : 'Ecografía'
  const rutaBandeja = rayosX ? '/rayos-x/gestion' : '/ecografia'
  const [vista, setVista] = useState('pendientes')
  const [busqueda, setBusqueda] = useState('')
  const [tipo, setTipo] = useState('todos')
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
  const tipos = [...new Set(estudios.map(e => e.tipo_estudio_nombre))].sort()

  return <main className="lab-page img-page">
    <div className="lab-main">
      <LaboratorioTopbar usuario={usuario} titulo={titulo} inicio={rutaBandeja} onLogout={logout} />
      <section className="lab-content">
        <div className="lab-title-row"><div><p className="lab-eyebrow">{rayosX ? 'RAYOS X' : 'ECOGRAFÍAS'}</p><h1>Bandeja de estudios</h1><p className="lab-intro">Consulta cada estudio y prepara o revisa su informe.</p></div></div>
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
          </div>
          {bandeja.isPending && <p role="status" className="img-mensaje">Cargando bandeja…</p>}
          {bandeja.isError && <p role="alert" className="img-mensaje">No se pudo cargar la bandeja.</p>}
          {bandeja.data && filtrados.length === 0 && <p className="img-mensaje">No hay estudios que coincidan con estos filtros.</p>}
          <div className="img-tarjetas">
            {filtrados.map(estudio => <article className="img-tarjeta" key={estudio.estudio_id}>
              <div className="img-tarjeta-cabecera"><div><p>{estudio.referencia_estudio}</p><h2>{estudio.tipo_estudio_nombre}</h2></div><span className={`lab-status lab-status--${estudio.estado}`}>{estadoEstudioImagen(estudio.estado)}</span></div>
              <dl><div><dt>Paciente</dt><dd>{estudio.paciente_nombre}</dd></div><div><dt>Solicitud</dt><dd>{estudio.referencia_solicitud}</dd></div><div><dt>Fecha</dt><dd>{new Date(estudio.fecha_solicitud).toLocaleDateString('es-BO')}</dd></div></dl>
              <div className="img-tarjeta-acciones"><Link className="lab-secondary-button" to={`${rutaBandeja}/estudios/${estudio.estudio_id}/informe`}>Ver informe</Link></div>
            </article>)}
          </div>
        </section>
      </section>
    </div>
  </main>
}
