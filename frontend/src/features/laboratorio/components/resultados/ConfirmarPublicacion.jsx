import ConfirmarAccion from '../ConfirmarAccion.jsx'
import { ETIQUETA_FUERA_DE_RANGO } from '../../utils/rangoReferencia.js'
import { parametrosVisibles } from '../../utils/captura.js'

/**
 * Resumen final antes de publicar. `estudios` es una lista de
 * { estudio_id, tipo_estudio_nombre, parametros } y `valores` el mapa parametro_id -> valor.
 */
export default function ConfirmarPublicacion({ estudios, valores, responsable, resumen, pendiente, onConfirmar, onCancelar }) {
  const fuera = new Map(resumen.fueraDeRango.map((item) => [item.id, item.estado]))
  return (
    <ConfirmarAccion titulo="Revisar y publicar resultados" textoConfirmar="Publicar resultados" textoCancelar="Seguir editando"
      pendiente={pendiente} onConfirmar={onConfirmar} onCancelar={onCancelar}>
      <p>Una vez publicados, el médico podrá verlos y <strong>no se podrán modificar</strong>. Comprueba los valores:</p>
      {estudios.map((estudio) => {
        const informados = parametrosVisibles(estudio.parametros).filter((parametro) => String(valores[parametro.id] ?? '').trim())
        return <section className="lab-confirm-study" key={estudio.estudio_id}>
          <h3>{estudio.tipo_estudio_nombre}</h3>
          {informados.length === 0 ? <p className="lab-form-hint">Sin valores informados.</p> : <table>
            <tbody>{informados.map((parametro) => <tr key={parametro.id} className={fuera.has(parametro.id) ? 'is-out-of-range' : undefined}>
              <th scope="row">{parametro.nombre}</th>
              <td>{valores[parametro.id]} {parametro.unidad}</td>
              <td>{fuera.has(parametro.id) ? ETIQUETA_FUERA_DE_RANGO[fuera.get(parametro.id)] : ''}</td>
            </tr>)}</tbody>
          </table>}
        </section>
      })}
      <p className="lab-form-hint">Responsable que publica: <strong>{responsable}</strong></p>
    </ConfirmarAccion>
  )
}
