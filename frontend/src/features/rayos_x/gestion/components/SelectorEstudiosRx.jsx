import { useEffect, useMemo, useRef, useState } from 'react'

export { erroresDeEstudios } from '../utils/solicitud.js'

const LATERALIDADES = [
  { codigo: 'derecha', nombre: 'Derecha' },
  { codigo: 'izquierda', nombre: 'Izquierda' },
  { codigo: 'bilateral', nombre: 'Bilateral' },
]

function nuevaConfiguracion(estudio) {
  // Sin lateralidad por defecto: el usuario debe elegirla (evita solicitar el lado equivocado).
  const lateralidad = null
  return {
    tipo_estudio_id: estudio.id,
    lateralidad,
    protocolo: '', // ya no se pide en la solicitud; las proyecciones se eligen directamente
    proyecciones: [],
    indicacion: '',
    observaciones: '',
    detalle_region: '',
  }
}

function nombreCategoria(catalogo, codigo) {
  return catalogo?.categorias?.find((categoria) => categoria.codigo === codigo)?.nombre ?? codigo ?? 'Otros estudios'
}

function useCatalogo(catalogo) {
  const estudios = useMemo(() => catalogo?.estudios?.filter((estudio) => estudio.activo !== false) ?? [], [catalogo])
  const porId = useMemo(() => new Map(estudios.map((estudio) => [Number(estudio.id), estudio])), [estudios])
  return { estudios, porId }
}

function sePuedeAnadir(estudio, valor) {
  const config = estudio.config ?? {}
  if (!config.requiere_lateralidad) return !valor.some((item) => Number(item.tipo_estudio_id) === Number(estudio.id))
  const opciones = ['derecha', 'izquierda', ...(config.permite_bilateral ? ['bilateral'] : [])]
  return opciones.some((lateralidad) => !valor.some((item) => Number(item.tipo_estudio_id) === Number(estudio.id) && item.lateralidad === lateralidad))
}

/** Catálogo: buscador y estudios agrupados por región; un clic añade el estudio. */
export function CatalogoEstudiosRx({ catalogo, valor, onChange, deshabilitado = false, titulo = '2. Estudios solicitados' }) {
  const [busqueda, setBusqueda] = useState('')
  const [region, setRegion] = useState('')
  const { estudios } = useCatalogo(catalogo)
  const termino = busqueda.trim().toLocaleLowerCase()
  const visibles = estudios.filter((estudio) => [estudio.nombre, estudio.codigo, estudio.config?.region]
    .some((campo) => campo?.toLocaleLowerCase().includes(termino)))
  const grupos = (catalogo?.categorias ?? []).map((categoria) => ({
    ...categoria,
    estudios: visibles.filter((estudio) => estudio.config?.categoria === categoria.codigo),
  })).filter((grupo) => grupo.estudios.length)
  const sinCategoria = visibles.filter((estudio) => !(catalogo?.categorias ?? [])
    .some((categoria) => categoria.codigo === estudio.config?.categoria))
  if (sinCategoria.length) grupos.push({ codigo: 'otros', nombre: 'Otros estudios', estudios: sinCategoria })
  const gruposVisibles = region ? grupos.filter((grupo) => grupo.codigo === region) : grupos

  return <section className="lab-form-section rxg-selector">
    <h3>{titulo}</h3>
    {!catalogo && <p className="lab-form-hint">Cargando catálogo de Rayos X...</p>}
    {catalogo && estudios.length === 0 && <p className="lab-form-hint">No hay estudios activos disponibles.</p>}
    <label className="lab-search-label">Buscar estudio
      <input type="search" value={busqueda} disabled={deshabilitado} onChange={(evento) => setBusqueda(evento.target.value)} placeholder="Nombre, código o región" />
    </label>
    {grupos.length > 1 && <div className="rxg-regiones" role="group" aria-label="Filtrar por región">
      <button type="button" aria-pressed={!region} onClick={() => setRegion('')}>Todas</button>
      {grupos.map((grupo) => <button key={grupo.codigo} type="button" aria-pressed={region === grupo.codigo} onClick={() => setRegion(grupo.codigo)}>{grupo.nombre}</button>)}
    </div>}
    <div className="rxg-catalogo" tabIndex={0} aria-label="Estudios disponibles">
      {gruposVisibles.map((grupo) => <section key={grupo.codigo} className="rxg-catalogo-grupo">
        <h4>{grupo.nombre}</h4>
        <div className="rxg-catalogo-opciones">{grupo.estudios.map((estudio) => {
          const disponible = sePuedeAnadir(estudio, valor)
          const cantidad = valor.filter((item) => Number(item.tipo_estudio_id) === Number(estudio.id)).length
          return <button key={estudio.id} type="button" className="rxg-catalogo-estudio" data-anadido={cantidad > 0 ? "" : undefined} disabled={deshabilitado || !disponible}
            onClick={() => onChange([...valor, nuevaConfiguracion(estudio)])}>
            <strong>{estudio.nombre}</strong>
            {cantidad > 0 && <span>{`✓ Añadido${cantidad > 1 ? ` (${cantidad})` : ''}${disponible ? ' · puedes añadir el otro lado' : ''}`}</span>}
          </button>
        })}</div>
      </section>)}
      {catalogo && termino && visibles.length === 0 && <p className="lab-form-hint">No hay estudios que coincidan con la búsqueda.</p>}
    </div>
  </section>
}

/** Estudios elegidos: lateralidad e indicación a la vista; lo demás, plegado en "Más opciones". */
export function EstudiosSeleccionadosRx({ catalogo, valor, onChange, deshabilitado = false, titulo }) {
  const { porId } = useCatalogo(catalogo)
  const contenedor = useRef(null)
  const anteriores = useRef(valor.length)

  // Al añadir un estudio, lleva la vista y el foco a su primer campo para completarlo de inmediato.
  useEffect(() => {
    if (valor.length > anteriores.current) {
      const tarjetas = contenedor.current?.querySelectorAll('fieldset.rxg-estudio-config')
      const nueva = tarjetas?.[tarjetas.length - 1]
      if (nueva) {
        const reducir = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
        nueva.scrollIntoView({ block: 'nearest', behavior: reducir ? 'auto' : 'smooth' })
        nueva.querySelector('select:not(:disabled), textarea:not(:disabled), input:not(:disabled)')?.focus({ preventScroll: true })
      }
    }
    anteriores.current = valor.length
  }, [valor.length])

  function actualizar(indice, cambios) {
    onChange(valor.map((item, posicion) => posicion === indice ? { ...item, ...cambios } : item))
  }

  function alternarProyeccion(indice, codigo) {
    const actuales = valor[indice].proyecciones ?? []
    actualizar(indice, { proyecciones: actuales.includes(codigo) ? actuales.filter((item) => item !== codigo) : [...actuales, codigo] })
  }

  return <section className="rxg-estudios-seleccionados" aria-live="polite" ref={contenedor}>
    <h3>{titulo ?? (valor.length ? `Estudios seleccionados (${valor.length})` : 'Estudios seleccionados')}</h3>
    {valor.length === 0 && <div className="rxg-vacio"><strong>Todavía no elegiste estudios</strong><span>Busca o toca un estudio del catálogo y aparecerá aquí para configurarlo.</span></div>}
    {valor.map((seleccion, indice) => {
      const estudio = porId.get(Number(seleccion.tipo_estudio_id))
      if (!estudio) return null
      const config = estudio.config ?? {}
      const lateralidadesUsadas = new Set(valor.filter((item, posicion) => posicion !== indice
        && Number(item.tipo_estudio_id) === Number(seleccion.tipo_estudio_id)).map((item) => item.lateralidad))
      const hayMas = (config.proyecciones?.length ?? 0) > 0
      return <fieldset className="rxg-estudio-config" key={`${seleccion.tipo_estudio_id}-${indice}`} disabled={deshabilitado}>
        <legend><span>{estudio.nombre}</span><small>{nombreCategoria(catalogo, config.categoria)}</small></legend>
        <button type="button" className="rxg-quitar" onClick={() => onChange(valor.filter((_, posicion) => posicion !== indice))}>Quitar</button>
        <div className="rxg-estudio-campos" data-sin-lateralidad={config.requiere_lateralidad ? undefined : ''}>
          {config.requiere_lateralidad && <label>Lateralidad
            <select required value={seleccion.lateralidad ?? ''} onChange={(evento) => actualizar(indice, { lateralidad: evento.target.value })}>
              <option value="" disabled>Selecciona</option>
              {LATERALIDADES.filter((item) => item.codigo !== 'bilateral' || config.permite_bilateral).map((item) =>
                <option key={item.codigo} value={item.codigo} disabled={lateralidadesUsadas.has(item.codigo)}>{item.nombre}</option>)}
            </select>
          </label>}
          <label className="rxg-campo-completo">Motivo o indicación clínica (opcional)
            <textarea rows="2" value={seleccion.indicacion ?? ''} onChange={(evento) => actualizar(indice, { indicacion: evento.target.value })} placeholder="¿Por qué se pide? Ej.: dolor tras una caída, control de fractura" />
          </label>
          {config.detalle_requerido && <label className="rxg-campo-completo">{config.detalle_requerido}
            <input required value={seleccion.detalle_region ?? ''} onChange={(evento) => actualizar(indice, { detalle_region: evento.target.value })} />
          </label>}
        </div>
        <details className="rxg-mas-opciones">
          <summary>Más opciones</summary>
          {hayMas && <fieldset className="rxg-proyecciones">
            <legend>Proyecciones solicitadas (opcional)</legend>
            <div>{config.proyecciones.map((proyeccion) => <label key={proyeccion.codigo} className="lab-checkbox-label">
              <input type="checkbox" checked={(seleccion.proyecciones ?? []).includes(proyeccion.codigo)} onChange={() => alternarProyeccion(indice, proyeccion.codigo)} />
              {proyeccion.nombre}
            </label>)}</div>
          </fieldset>}
          <label className="rxg-campo-completo">Observaciones
            <textarea rows="2" value={seleccion.observaciones ?? ''} onChange={(evento) => actualizar(indice, { observaciones: evento.target.value })} />
          </label>
        </details>
        {(config.notas?.length ?? 0) > 0 && <ul className="rxg-notas">{config.notas.map((nota) => <li key={nota}>{nota}</li>)}</ul>}
      </fieldset>
    })}
  </section>
}

/** Versión conjunta (catálogo + elegidos) para la solicitud del médico desde la ficha. */
export default function SelectorEstudiosRx({ catalogo, valor, onChange, deshabilitado = false, numeracion = '2. ' }) {
  return <>
    <CatalogoEstudiosRx catalogo={catalogo} valor={valor} onChange={onChange} deshabilitado={deshabilitado} titulo={`${numeracion}Estudios solicitados`} />
    <EstudiosSeleccionadosRx catalogo={catalogo} valor={valor} onChange={onChange} deshabilitado={deshabilitado} />
  </>
}
