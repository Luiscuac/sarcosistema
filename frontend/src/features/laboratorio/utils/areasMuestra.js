const areasSangre = new Set(['hematologia', 'bioquimica', 'serologia'])

export function areasParaMuestra(estudios, tipoMuestra) {
  const compatibles = estudios.filter((estudio) => {
    if (tipoMuestra === 'Sangre') return areasSangre.has(estudio.categoria_laboratorio)
    if (tipoMuestra === 'Orina') return estudio.tipo_estudio_codigo === 'EGO'
    if (tipoMuestra === 'Heces') return estudio.categoria_laboratorio === 'copro_orina' && estudio.tipo_estudio_codigo !== 'EGO'
    return false
  })
  const porArea = new Map()
  for (const estudio of compatibles) {
    const nombre = tipoMuestra === 'Sangre' ? estudio.categoria_laboratorio : tipoMuestra
    if (!porArea.has(nombre)) porArea.set(nombre, [])
    porArea.get(nombre).push(estudio)
  }
  return [...porArea].map(([codigo, items]) => ({ codigo, estudios: items }))
}
