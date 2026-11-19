export function aplicarPropuestaEcografia(datos, item) {
  if (item.organo) {
    const anterior = datos.evaluaciones?.[item.organo] || ''
    return {
      anterior,
      datos: {
        ...datos,
        evaluaciones: {
          ...datos.evaluaciones,
          [item.organo]: anterior.trim() ? `${anterior.trim()}\n${item.valor}` : item.valor,
        },
      },
    }
  }
  if (!['zona', 'observaciones', 'conclusion'].includes(item.campo)) return null
  const anterior = datos[item.campo] || ''
  return {
    anterior,
    datos: {
      ...datos,
      [item.campo]: anterior.trim() ? `${anterior.trim()}\n${item.valor}` : item.valor,
    },
  }
}

export function deshacerPropuestaEcografia(datos, item, anterior) {
  const actual = item.organo ? datos.evaluaciones?.[item.organo] || '' : datos[item.campo] || ''
  const esperado = anterior.trim() ? `${anterior.trim()}\n${item.valor}` : item.valor
  if (actual !== esperado) return null
  if (item.organo) {
    return {
      ...datos,
      evaluaciones: { ...datos.evaluaciones, [item.organo]: anterior },
    }
  }
  if (!['zona', 'observaciones', 'conclusion'].includes(item.campo)) return datos
  return { ...datos, [item.campo]: anterior }
}
