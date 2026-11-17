import { useMemo, useState } from 'react'

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
    protocolo: '',
    proyecciones: [],
    indicacion: '',
    observaciones: '',
    detalle_region: '',
  }
}

function nombreCategoria(catalogo, codigo) {
  return catalogo?.categorias?.find((categoria) => categoria.codigo === codigo)?.nombre ?? codigo ?? 'Otros estudios'
}

export default function SelectorEstudiosRx({ catalogo, valor, onChange, deshabilitado = false, numeracion = '2. ' }) {
  const [busqueda, setBusqueda] = useState('')
  const estudios = catalogo?.estudios?.filter((estudio) => estudio.activo !== false) ?? []
  const porId = useMemo(() => new Map(estudios.map((estudio) => [Number(estudio.id), estudio])), [estudios])
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

  function actualizar(indice, cambios) {
    onChange(valor.map((item, posicion) => posicion === indice ? { ...item, ...cambios } : item))
  }

  function elegirProtocolo(indice, estudio, codigo) {
    const protocolo = estudio.config?.protocolos?.find((item) => item.codigo === codigo)
    actualizar(indice, { protocolo: codigo, proyecciones: protocolo ? [...protocolo.proyecciones] : [] })
  }

  function alternarProyeccion(indice, codigo) {
    const actuales = valor[indice].proyecciones ?? []
    actualizar(indice, { proyecciones: actuales.includes(codigo) ? actuales.filter((item) => item !== codigo) : [...actuales, codigo] })
  }

  function sePuedeAnadir(estudio) {
    const config = estudio.config ?? {}
    if (!config.requiere_lateralidad) return !valor.some((item) => Number(item.tipo_estudio_id) === Number(estudio.id))
    const opciones = ['derecha', 'izquierda', ...(config.permite_bilateral ? ['bilateral'] : [])]
    return opciones.some((lateralidad) => !valor.some((item) => Number(item.tipo_estudio_id) === Number(estudio.id) && item.lateralidad === lateralidad))
  }

  return <section className="lab-form-section rxg-selector">
    <h3>{numeracion}Estudios solicitados</h3>
    {!catalogo && <p className="lab-form-hint">Cargando catálogo de Rayos X...</p>}
    {catalogo && estudios.length === 0 && <p className="lab-form-hint">No hay estudios activos disponibles.</p>}
    <label className="lab-search-label">Buscar estudio
      <input type="search" value={busqueda} disabled={deshabilitado} onChange={(evento) => setBusqueda(evento.target.value)} placeholder="Nombre, código o región" />
    </label>
    <div className="rxg-catalogo">
      {grupos.map((grupo) => <section key={grupo.codigo} className="rxg-catalogo-grupo">
        <h4>{grupo.nombre}</h4>
        <div className="rxg-catalogo-opciones">{grupo.estudios.map((estudio) => {
          const disponible = sePuedeAnadir(estudio)
          return <button key={estudio.id} type="button" className="rxg-catalogo-estudio" disabled={deshabilitado || !disponible}
            onClick={() => onChange([...valor, nuevaConfiguracion(estudio)])}>
            <strong>{estudio.nombre}</strong><span>{disponible ? 'Añadir estudio' : 'Ya se eligieron las opciones disponibles'}</span>
          </button>
        })}</div>
      </section>)}
      {catalogo && termino && visibles.length === 0 && <p className="lab-form-hint">No hay estudios que coincidan con la búsqueda.</p>}
    </div>

    <div className="rxg-estudios-seleccionados" aria-live="polite">
      <h4>{valor.length ? `Estudios seleccionados (${valor.length})` : 'Ningún estudio seleccionado todavía'}</h4>
      {valor.map((seleccion, indice) => {
        const estudio = porId.get(Number(seleccion.tipo_estudio_id))
        if (!estudio) return null
        const config = estudio.config ?? {}
        const lateralidadesUsadas = new Set(valor.filter((item, posicion) => posicion !== indice
          && Number(item.tipo_estudio_id) === Number(seleccion.tipo_estudio_id)).map((item) => item.lateralidad))
        return <fieldset className="rxg-estudio-config" key={`${seleccion.tipo_estudio_id}-${indice}`} disabled={deshabilitado}>
          <legend><span>{estudio.nombre}</span><small>{nombreCategoria(catalogo, config.categoria)}</small></legend>
          <button type="button" className="rxg-quitar" onClick={() => onChange(valor.filter((_, posicion) => posicion !== indice))}>Quitar</button>
          <div className="lab-form-grid">
            {config.requiere_lateralidad && <label>Lateralidad
              <select required value={seleccion.lateralidad ?? ''} onChange={(evento) => actualizar(indice, { lateralidad: evento.target.value })}>
                <option value="" disabled>Selecciona</option>
                {LATERALIDADES.filter((item) => item.codigo !== 'bilateral' || config.permite_bilateral).map((item) =>
                  <option key={item.codigo} value={item.codigo} disabled={lateralidadesUsadas.has(item.codigo)}>{item.nombre}</option>)}
              </select>
            </label>}
            {(config.protocolos?.length ?? 0) > 0 && <label>Protocolo
              <select value={seleccion.protocolo ?? ''} onChange={(evento) => elegirProtocolo(indice, estudio, evento.target.value)}>
                <option value="">Sin protocolo predefinido</option>
                {config.protocolos.map((protocolo) => <option key={protocolo.codigo} value={protocolo.codigo}>{protocolo.nombre}</option>)}
              </select>
            </label>}
            {config.detalle_requerido && <label className="lab-full-field">{config.detalle_requerido}
              <input required value={seleccion.detalle_region ?? ''} onChange={(evento) => actualizar(indice, { detalle_region: evento.target.value })} />
            </label>}
            {(config.proyecciones?.length ?? 0) > 0 && <fieldset className="rxg-proyecciones lab-full-field">
              <legend>Proyecciones solicitadas</legend>
              <div>{config.proyecciones.map((proyeccion) => <label key={proyeccion.codigo} className="lab-checkbox-label">
                <input type="checkbox" checked={(seleccion.proyecciones ?? []).includes(proyeccion.codigo)} onChange={() => alternarProyeccion(indice, proyeccion.codigo)} />
                {proyeccion.nombre}
              </label>)}</div>
            </fieldset>}
            <label className="lab-full-field">Indicación clínica
              <textarea rows="2" value={seleccion.indicacion ?? ''} onChange={(evento) => actualizar(indice, { indicacion: evento.target.value })} />
            </label>
            <label className="lab-full-field">Observaciones
              <textarea rows="2" value={seleccion.observaciones ?? ''} onChange={(evento) => actualizar(indice, { observaciones: evento.target.value })} />
            </label>
          </div>
          {(config.notas?.length ?? 0) > 0 && <ul className="rxg-notas">{config.notas.map((nota) => <li key={nota}>{nota}</li>)}</ul>}
        </fieldset>
      })}
    </div>
  </section>
}
