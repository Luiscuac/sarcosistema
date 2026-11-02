import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listarResultadosPublicados } from '../api/laboratorioApi.js'
import { useExamenes } from '../hooks/useExamenes.js'
import { agruparSolicitudes } from '../utils/agruparSolicitudes.js'
import SolicitudRow from './solicitudes/SolicitudRow.jsx'

export default function SolicitudesPanel({ onRecibirMuestra, onAbrirResultado }) {
  const [busqueda, setBusqueda] = useState('')
  const [vista, setVista] = useState('pendientes')
  const [solicitudAbierta, setSolicitudAbierta] = useState(null)
  const { data: estudios = [], isLoading, isError } = useExamenes()
  const publicadosQuery = useQuery({ queryKey: ['examenes', 'publicados'], queryFn: listarResultadosPublicados, enabled: vista === 'publicados' })
  const estudiosActuales = vista === 'pendientes' ? estudios : publicadosQuery.data ?? []
  const cargando = vista === 'pendientes' ? isLoading : publicadosQuery.isLoading
  const error = vista === 'pendientes' ? isError : publicadosQuery.isError
  const solicitudes = useMemo(() => agruparSolicitudes(estudiosActuales), [estudiosActuales])
  const visibles = useMemo(() => {
    const termino = busqueda.trim().toLocaleLowerCase()
    if (!termino) return solicitudes
    return solicitudes.filter((solicitud) =>
      [solicitud.paciente_nombre, solicitud.referencia,
        ...solicitud.estudios.flatMap((estudio) => [estudio.referencia_estudio, estudio.tipo_estudio_nombre])]
        .some((valor) => valor?.toLocaleLowerCase().includes(termino)),
    )
  }, [busqueda, solicitudes])

  return (
    <div className="lab-list-panel">
      <div className="lab-list-toolbar">
        <div>
          <h2>{vista === 'pendientes' ? 'Solicitudes pendientes' : 'Resultados publicados'}</h2>
          <p>Una fila por solicitud. Abre la solicitud para trabajar cada estudio.</p>
        </div>
      </div>
      <div className="lab-list-tabs" role="tablist" aria-label="Filtrar solicitudes">
        <button type="button" role="tab" aria-selected={vista === 'pendientes'} className={vista === 'pendientes' ? 'is-active' : ''} onClick={() => { setVista('pendientes'); setSolicitudAbierta(null) }}>Pendientes</button>
        <button type="button" role="tab" aria-selected={vista === 'publicados'} className={vista === 'publicados' ? 'is-active' : ''} onClick={() => { setVista('publicados'); setSolicitudAbierta(null) }}>Publicados</button>
      </div>
      <input
        className="lab-search"
        type="search"
        placeholder="Buscar paciente, solicitud o estudio"
        value={busqueda}
        onChange={(event) => setBusqueda(event.target.value)}
        aria-label="Buscar paciente, solicitud o estudio"
      />
      <div className="lab-table-wrap">
        <table className="lab-table">
          <caption className="sr-only">{vista === 'pendientes' ? 'Solicitudes pendientes de laboratorio' : 'Resultados publicados de laboratorio'}</caption>
          <thead>
            <tr><th>Solicitud / paciente</th><th>Estado</th><th>Estudios</th><th>Prioridad</th><th>Acción</th></tr>
          </thead>
          <tbody>
            {cargando && <tr><td className="lab-empty" colSpan="5"><strong>Cargando solicitudes…</strong></td></tr>}
            {error && <tr><td className="lab-empty" colSpan="5">
              <strong>No se pudo cargar la bandeja.</strong>
              <span>Comprueba que el backend y la base estén activos e inténtalo de nuevo.</span>
            </td></tr>}
            {!cargando && !error && visibles.length === 0 && <tr><td className="lab-empty" colSpan="5">
              <strong>{busqueda ? 'No hay resultados para esa búsqueda.' : vista === 'pendientes' ? 'No hay solicitudes pendientes.' : 'Todavía no hay resultados publicados.'}</strong>
              <span>{busqueda ? 'Prueba con otro nombre o referencia.' : vista === 'pendientes' ? 'Las solicitudes aparecerán aquí cuando se registren.' : 'Los resultados aparecerán aquí después de su publicación.'}</span>
            </td></tr>}
            {!cargando && !error && visibles.map((solicitud) => {
              const abierta = solicitudAbierta === solicitud.id
              return <SolicitudRow key={solicitud.id} solicitud={solicitud} abierta={abierta} vista={vista}
                onToggle={() => setSolicitudAbierta(abierta ? null : solicitud.id)}
                onRecibirMuestra={onRecibirMuestra} onAbrirResultado={onAbrirResultado} />
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
