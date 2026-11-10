/** Utilidades de examenes complementarios (imagen, DICOM y formatos futuros). */

const UNIDADES = ['B', 'KB', 'MB', 'GB']

export function formatearTamano(bytes) {
  if (!Number.isFinite(bytes) || bytes < 0) return '---'
  if (bytes < 1024) return `${bytes} B`
  let valor = bytes / 1024
  let indice = 1
  while (valor >= 1024 && indice < UNIDADES.length - 1) {
    valor /= 1024
    indice += 1
  }
  return `${valor.toFixed(valor >= 10 ? 0 : 1)} ${UNIDADES[indice]}`
}

/** El navegador no puede mostrar DICOM: se ofrece como descarga. */
export function esDescargable(mime) {
  return !String(mime || '').startsWith('image/')
}

export function etiquetaArchivo(mime, nombre) {
  if (esDescargable(mime)) {
    if (String(mime).includes('dicom')) return 'DICOM (descargar)'
    if (String(mime).includes('pdf')) return 'PDF (descargar)'
    return 'Archivo (descargar)'
  }
  return nombre
}

export function estadoEstudioImagen(estado) {
  return {
    pendiente_muestra: 'Pendiente de realizar',
    resultado_en_preparacion: 'Informe en preparación',
    publicado: 'Publicado',
    invalidado: 'Invalidado',
    no_realizado: 'No realizado',
  }[estado] || estado
}
