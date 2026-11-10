import { useId } from 'react'
import { ETIQUETA_FUERA_DE_RANGO, evaluarValor } from '../../utils/rangoReferencia.js'
import './captura.css'

const MODO_TECLADO = { decimal: 'decimal', entero: 'numeric' }

/**
 * Un parámetro del formato de resultados. Los numéricos usan texto con teclado
 * numérico: aceptan coma decimal y la rueda del mouse no altera el valor.
 */
export default function CampoResultado({ parametro, valor, onCambiar, deshabilitado }) {
  const ayudaId = useId()
  const fueraDeRango = evaluarValor(valor, parametro.rango_referencia, parametro.tipo_entrada)
  const referencia = [parametro.unidad, parametro.rango_referencia].filter(Boolean).join(' · ')
  const comunes = {
    value: valor ?? '',
    disabled: deshabilitado,
    onChange: (evento) => onCambiar(evento.target.value),
    'data-campo-resultado': true,
    'aria-describedby': referencia || fueraDeRango ? ayudaId : undefined,
  }

  return (
    <label className={fueraDeRango ? 'lab-result-field is-out-of-range' : 'lab-result-field'}>
      <span>{parametro.nombre}{parametro.obligatorio && <abbr title="Obligatorio"> *</abbr>}</span>
      {parametro.opciones?.length
        ? <select {...comunes}>
          <option value="">Seleccionar resultado</option>
          {parametro.opciones.map((opcion) => <option key={opcion} value={opcion}>{opcion}</option>)}
        </select>
        : <input {...comunes} type="text" inputMode={MODO_TECLADO[parametro.tipo_entrada]} autoComplete="off" maxLength={2000} />}
      <small id={ayudaId}>
        {referencia}
        {fueraDeRango && <strong className="lab-range-flag"> {ETIQUETA_FUERA_DE_RANGO[fueraDeRango]} · revisa antes de publicar</strong>}
      </small>
    </label>
  )
}
