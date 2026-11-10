import { useExamenes } from '../hooks/useExamenes.js'
import { agruparSolicitudes } from '../utils/agruparSolicitudes.js'
import { INDICADORES_BANDEJA } from '../utils/bandeja.js'

/** Indicadores de la bandeja; cada tarjeta filtra la tabla al pulsarla. */
export default function ResumenSolicitudes({ indicadorActivo, onSeleccionar }) {
  const { data: estudios = [], isLoading, isError } = useExamenes()
  const solicitudes = agruparSolicitudes(estudios)

  return (
    <div className="lab-summary" aria-label="Indicadores de laboratorio">
      {INDICADORES_BANDEJA.map((indicador) => {
        const activo = indicadorActivo === indicador.codigo
        return <button type="button" key={indicador.codigo} aria-pressed={activo}
          className={activo ? 'lab-summary-card is-active' : 'lab-summary-card'}
          onClick={() => onSeleccionar(activo ? 'todas' : indicador.codigo)}>
          <strong>{isLoading ? '…' : isError ? '—' : solicitudes.filter(indicador.cumple).length}</strong>
          <span>{indicador.nombre}</span>
          {isError && <small>No disponible</small>}
        </button>
      })}
    </div>
  )
}
