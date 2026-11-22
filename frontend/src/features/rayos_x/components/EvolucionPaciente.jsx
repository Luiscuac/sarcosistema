import { useQuery } from '@tanstack/react-query'
import { obtenerEvolucion } from '../api/rayosXAiApi.js'
import { lecturaEvolucion, NIVELES_TRIAJE } from '../analisis.js'

const fecha = valor => (valor ? new Date(valor).toLocaleDateString('es-BO') : '—')

/** Comparación con radiografías de tórax anteriores del mismo paciente (triaje ya calculado; no ejecuta modelos). */
export default function EvolucionPaciente({ estudioId, usuarioId }) {
  const consulta = useQuery({
    queryKey: ['imagenes', usuarioId, 'evolucion', estudioId],
    queryFn: ({ signal }) => obtenerEvolucion(estudioId, signal),
    retry: false,
  })
  const datos = consulta.data
  // Sin anteriores, sin triaje o sin artefacto: no ocupa espacio (no es un error para el médico).
  if (!datos?.comparacion) return null
  const l = lecturaEvolucion(datos)
  return <section className="rx-ia-evolucion" aria-label="Comparación con radiografías anteriores">
    <h4>Comparado con la radiografía anterior <small>{l.hace}{l.referencia ? ` · ${l.referencia}` : ''}</small></h4>
    {l.indice && <p className={`rx-ia-evolucion-tendencia es-${l.indice.clave}`}><strong>{l.indice.texto}</strong></p>}
    {l.tb && <p className="rx-ia-evolucion-tb">{l.tb}</p>}
    {l.categorias.length > 0 && <p className="rx-ia-evolucion-subtitulo">Señales que cambiaron más que el margen de una re-toma:</p>}
    {l.categorias.length > 0 && <ul className="rx-ia-evolucion-cambios">{l.categorias.map(c => <li key={c}>{c}</li>)}</ul>}
    {l.avisos.map(a => <p key={a} className="rx-nota">{a}</p>)}
    <details className="rx-ia-plegable">
      <summary>Ver radiografías anteriores ({datos.anteriores.length})</summary>
      <table className="rx-ia-evolucion-tabla">
        <thead><tr><th>Fecha</th><th>Estudio</th><th>Prioridad</th><th>Índice</th><th>Patrón TB</th></tr></thead>
        <tbody>{[datos.actual, ...datos.anteriores].map((p, i) => <tr key={p.estudio_id} className={i === 0 ? 'es-actual' : undefined}>
          <td>{fecha(p.fecha)}{i === 0 ? ' (esta)' : ''}</td>
          <td>{p.referencia}</td>
          <td>{NIVELES_TRIAJE[p.nivel]?.texto || '—'}</td>
          <td>{typeof p.indice === 'number' ? `${Math.round(p.indice * 100)} de 100` : '—'}</td>
          <td>{p.patron_tb_nivel === 'compatible' ? 'Aviso' : '—'}</td>
        </tr>)}</tbody>
      </table>
    </details>
    <p className="rx-nota">{datos.advertencia}</p>
  </section>
}
