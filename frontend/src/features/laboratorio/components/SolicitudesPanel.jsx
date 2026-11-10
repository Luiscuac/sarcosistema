import { useMemo, useState } from 'react'
import { useExamenes, useExamenesFinalizados } from '../hooks/useExamenes.js'
import { agruparSolicitudes } from '../utils/agruparSolicitudes.js'
import { filtrarSolicitudes, INDICADORES_BANDEJA, PERIODOS_FINALIZADAS } from '../utils/bandeja.js'
import { useAhora } from '../../../shared/hooks/useAhora.js'
import SolicitudRow from './solicitudes/SolicitudRow.jsx'

function MensajeVacio({ busqueda, vista, filtrado }) {
  if (busqueda || filtrado) {
    return <><strong>No hay solicitudes con esos filtros.</strong><span>Prueba con otro nombre, referencia o quita el filtro activo.</span></>
  }
  return vista === 'pendientes'
    ? <><strong>No hay solicitudes pendientes.</strong><span>Las nuevas solicitudes aparecerán aquí automáticamente.</span></>
    : <><strong>Todavía no hay solicitudes finalizadas.</strong><span>Aparecerán aquí cuando todos sus estudios estén publicados o cerrados como no realizados.</span></>
}

export default function SolicitudesPanel({ vista, onVistaChange, indicador, onIndicadorChange }) {
  const [busqueda, setBusqueda] = useState('')
  const [periodo, setPeriodo] = useState('semana')
  const ahora = useAhora()
  const pendientesQuery = useExamenes()
  const finalizadasQuery = useExamenesFinalizados(vista === 'finalizadas')
  const consulta = vista === 'pendientes' ? pendientesQuery : finalizadasQuery
  const estudios = consulta.data
  const solicitudes = useMemo(() => agruparSolicitudes(estudios ?? []), [estudios])
  const visibles = filtrarSolicitudes(solicitudes, {
    busqueda,
    indicador: vista === 'pendientes' ? indicador : 'todas',
    periodo: vista === 'finalizadas' ? periodo : 'todas',
    ahora,
  })
  const filtroActivo = vista === 'pendientes' && indicador !== 'todas'
    ? INDICADORES_BANDEJA.find(({ codigo }) => codigo === indicador)
    : null

  return (
    <div className="lab-list-panel">
      <div className="lab-list-toolbar">
        <h2>{vista === 'pendientes' ? 'Solicitudes pendientes' : 'Solicitudes finalizadas'}</h2>
        <span className="lab-pending-tag">{consulta.isFetching && !consulta.isLoading ? 'Actualizando…' : 'Se actualiza automáticamente'}</span>
      </div>
      <div className="lab-list-tabs" role="tablist" aria-label="Filtrar solicitudes">
        <button type="button" role="tab" aria-selected={vista === 'pendientes'} className={vista === 'pendientes' ? 'is-active' : ''} onClick={() => onVistaChange('pendientes')}>Pendientes</button>
        <button type="button" role="tab" aria-selected={vista === 'finalizadas'} className={vista === 'finalizadas' ? 'is-active' : ''} onClick={() => onVistaChange('finalizadas')}>Finalizadas</button>
      </div>
      <div className="lab-list-filters">
        <input className="lab-search" type="search" placeholder="Buscar paciente, solicitud o estudio" value={busqueda}
          onChange={(evento) => setBusqueda(evento.target.value)} aria-label="Buscar paciente, solicitud o estudio" />
        {vista === 'finalizadas' && <label className="lab-period">Periodo
          <select value={periodo} onChange={(evento) => setPeriodo(evento.target.value)}>
            {PERIODOS_FINALIZADAS.map(({ codigo, nombre }) => <option key={codigo} value={codigo}>{nombre}</option>)}
          </select>
        </label>}
      </div>
      {filtroActivo && <p className="lab-active-filter">
        Mostrando: <strong>{filtroActivo.nombre.toLocaleLowerCase()}</strong>
        <button type="button" onClick={() => onIndicadorChange('todas')}>Quitar filtro ×</button>
      </p>}
      <div className="lab-table-wrap">
        <table className="lab-table">
          <caption className="sr-only">{vista === 'pendientes' ? 'Solicitudes pendientes de laboratorio' : 'Solicitudes finalizadas de laboratorio'}</caption>
          <thead>
            <tr><th>Paciente / solicitud</th><th>Estado</th><th>Avance</th><th>Prioridad</th><th>Siguiente paso</th></tr>
          </thead>
          <tbody>
            {consulta.isLoading && <tr><td className="lab-empty" colSpan="5"><strong>Cargando solicitudes…</strong></td></tr>}
            {consulta.isError && <tr><td className="lab-empty" colSpan="5">
              <strong>No se pudo cargar la bandeja.</strong>
              <span>Comprueba la conexión. Se volverá a intentar automáticamente.</span>
            </td></tr>}
            {consulta.isSuccess && visibles.length === 0 && <tr><td className="lab-empty" colSpan="5">
              <MensajeVacio busqueda={busqueda.trim()} vista={vista} filtrado={Boolean(filtroActivo) || (vista === 'finalizadas' && periodo !== 'todas')} />
            </td></tr>}
            {consulta.isSuccess && visibles.map((solicitud) => <SolicitudRow key={solicitud.id} solicitud={solicitud} ahora={ahora} />)}
          </tbody>
        </table>
      </div>
    </div>
  )
}
