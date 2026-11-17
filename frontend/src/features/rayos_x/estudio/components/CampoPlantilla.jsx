import { useEffect, useId, useRef } from 'react'
import { insertarFrase } from '../utils/informe.js'

export default function CampoPlantilla({ campo, valor, onChange, disabled = false, destacado = false }) {
  const ayudaId = useId()
  const area = useRef(null)
  useEffect(() => {
    if (!area.current) return
    area.current.style.height = 'auto'
    area.current.style.height = `${area.current.scrollHeight}px`
  }, [valor])
  const comunes = { value: valor ?? '', disabled, onChange: e => onChange(campo.tipo === 'medicion' && e.target.value !== '' ? Number(e.target.value) : e.target.value), 'aria-describedby': campo.ayuda ? ayudaId : undefined }
  return <div className={`rxe-campo${destacado ? ' rxe-campo--destacado' : ''}`}>
    <label htmlFor={`rxe-${campo.clave}`}>{campo.titulo}{campo.clave === 'conclusion' && ' *'}</label>
    {campo.tipo === 'opcion' ? <select id={`rxe-${campo.clave}`} {...comunes}>
      <option value="">Seleccionar</option>{(campo.opciones || []).map(opcion => <option key={opcion}>{opcion}</option>)}
    </select> : campo.tipo === 'medicion' ? <div className="rxe-medicion">
      <input id={`rxe-${campo.clave}`} type="number" min={campo.minimo} max={campo.maximo} step="any" {...comunes} />
      {campo.unidad && <span>{campo.unidad}</span>}
    </div> : <textarea ref={area} id={`rxe-${campo.clave}`} rows={3} maxLength={12000} {...comunes} />}
    {campo.ayuda && <small id={ayudaId}>{campo.ayuda}</small>}
    {!disabled && campo.frases?.length > 0 && <div className="rxe-frases" aria-label={`Frases para ${campo.titulo}`}>
      {campo.frases.map(frase => <button key={frase} type="button" className="lab-secondary-button"
        onClick={() => onChange(insertarFrase(valor, frase))}>Insertar: {frase}</button>)}
    </div>}
  </div>
}
