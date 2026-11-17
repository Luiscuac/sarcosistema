const vacio = valor => valor == null || (typeof valor === 'string' && !valor.trim())

export function estadoInicialInforme(informe, plantilla = {}) {
  const generales = Object.fromEntries((plantilla.generales || []).map(campo => [campo.clave, '']))
  const apartados = Object.fromEntries((plantilla.apartados || []).map(campo => [campo.clave, '']))
  if (informe?.estructurado !== false) {
    Object.assign(generales, informe?.contenido?.generales || {})
    Object.assign(apartados, informe?.contenido?.apartados || {})
  }
  return {
    contenido: { generales, apartados },
    textoFinal: informe?.estructurado === false && informe?.estado === 'borrador'
      ? informe.texto || ''
      : informe?.texto_personalizado ? informe.texto || '' : null,
  }
}

export function limpiarContenido(contenido = {}) {
  const limpiarGrupo = grupo => Object.fromEntries(Object.entries(grupo || {})
    .filter(([, valor]) => !vacio(valor))
    .map(([clave, valor]) => [clave, typeof valor === 'string' ? valor.trim() : valor]))
  return { generales: limpiarGrupo(contenido.generales), apartados: limpiarGrupo(contenido.apartados) }
}

export function detectarCambios(actual, inicial) {
  return JSON.stringify({ contenido: limpiarContenido(actual.contenido), textoFinal: actual.textoFinal ?? null }) !==
    JSON.stringify({ contenido: limpiarContenido(inicial.contenido), textoFinal: inicial.textoFinal ?? null })
}

export function insertarFrase(texto, frase) {
  const base = String(texto || '').trimEnd()
  return base ? `${base}${/[.!?]$/.test(base) ? ' ' : '. '}${frase}` : frase
}

const unirNatural = valores => valores.length < 2 ? (valores[0] || '') : `${valores.slice(0, -1).join(', ')} y ${valores.at(-1)}`
export function fraseTecnicaDesdeAdquisicion(detalle) {
  const codigos = detalle?.adquisicion?.proyecciones_realizadas || []
  const nombres = codigos.map(codigo => detalle?.config?.proyecciones?.find(p => p.codigo === codigo)?.nombre || codigo)
  if (!nombres.length) return ''
  const examen = detalle?.estudio?.tipo_estudio_nombre || 'Radiografía'
  const lateralidad = detalle?.adquisicion?.lateralidad_realizada || detalle?.estudio?.detalle?.lateralidad
  return `${examen}. Proyecciones ${unirNatural(nombres)}${lateralidad ? `, lateralidad ${lateralidad}` : ''}.`
}

export function parametrosANumeros(parametros = {}) {
  return Object.fromEntries(Object.entries(parametros).flatMap(([clave, valor]) => {
    if (vacio(valor)) return []
    if (clave === 'equipo') return [[clave, String(valor).trim()]]
    const numero = Number(valor)
    return Number.isFinite(numero) ? [[clave, numero]] : []
  }))
}

const IMAGEN_MAX = 15 * 1024 * 1024
const DICOM_MAX = 100 * 1024 * 1024
export function validarArchivoImagen(archivo) {
  const nombre = archivo?.name?.toLowerCase() || ''
  const dicom = nombre.endsWith('.dcm') || ['application/dicom', 'application/dicom+json'].includes(archivo?.type)
  const imagen = ['image/jpeg', 'image/png'].includes(archivo?.type) || /\.(jpe?g|png)$/.test(nombre)
  if (!dicom && !imagen) return 'Formato no admitido. Usa JPG, PNG o DICOM (.dcm).'
  if (archivo.size > (dicom ? DICOM_MAX : IMAGEN_MAX)) return dicom
    ? 'El archivo DICOM supera 100 MB.' : 'La imagen supera 15 MB.'
  return null
}

export function partirTextoInforme(texto = '') {
  const secciones = []
  let actual = { titulo: null, lineas: [] }
  String(texto).split(/\r?\n/).forEach(linea => {
    const limpia = linea.trim()
    if (limpia && limpia === limpia.toUpperCase() && limpia.endsWith(':')) {
      if (actual.titulo || actual.lineas.length) secciones.push(actual)
      actual = { titulo: limpia.slice(0, -1), lineas: [] }
    } else actual.lineas.push(linea)
  })
  if (actual.titulo || actual.lineas.length) secciones.push(actual)
  return secciones
}
