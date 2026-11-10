// Se ejecuta después de imagenes.browser.js en la misma sesión ficticia.
// API real para conflicto; solo el retiro del archivo se simula en el GET de detalle.
async (page) => {
  const fs = page.constructor.constructor('return process')().getBuiltinModule('fs')
  const config = JSON.parse(fs.readFileSync('backend/.radiologia-resultados/integracion-browser-config.json', 'utf8'))
  const datos = await page.evaluate(async api => {
    const headers = { Authorization: `Bearer ${sessionStorage.getItem('token')}` }
    const lista = await (await fetch(`${api}/imagenes/estudios`, { headers })).json()
    const estudio = lista.estudios.find(e => e.referencia === 'RX-DEMO-IA-001')
    const detalle = await (await fetch(`${api}/imagenes/estudios/${estudio.id}`, { headers })).json()
    const analisis = await (await fetch(`${api}/imagenes/analisis/${detalle.analisis_reciente}`, { headers })).json()
    return { estudio: estudio.id, analisis: analisis.id, version: analisis.version_revision }
  }, config.api)
  await page.getByLabel('Decisión', { exact: true }).selectOption('corregida')
  await page.getByLabel('Motivo', { exact: true }).fill('Borrador ficticio de la primera pestaña')
  await page.getByLabel('Corrección de la propuesta').fill('Corrección ficticia pendiente de revisión, no diagnóstico.')
  const guardado = await page.evaluate(async ({ api, datos }) => {
    const r = await fetch(`${api}/imagenes/analisis/${datos.analisis}/revision`, {
      method: 'POST', headers: { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ version: datos.version, decision: 'rechazada', motivo: 'Simulación de otra pestaña, revisión real persistida.' }),
    })
    return r.status
  }, { api: config.api, datos })
  if (guardado !== 200) throw new Error('No se pudo generar la revisión concurrente real')
  const reenfocar = () => page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' })
    window.dispatchEvent(new Event('visibilitychange'))
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' })
    window.dispatchEvent(new Event('visibilitychange'))
    delete document.visibilityState
  })
  await reenfocar()
  await page.getByText(new RegExp(`Versión ${datos.version + 1}: rechazada`)).waitFor()
  await page.getByText('Hay una revisión más reciente. Tu borrador conserva su versión original y no se guardará encima.', { exact: true }).waitFor()
  if (!await page.getByRole('button', { name: 'Guardar revisión explícita' }).isDisabled()) throw new Error('El refetch habilitó un borrador obsoleto')
  if (!await page.getByLabel('Motivo', { exact: true }).inputValue()) throw new Error('Se descartó el borrador sin permiso')
  const path = `${config.api}/imagenes/estudios/${datos.estudio}`
  await page.route(path, async route => {
    const respuesta = await route.fetch()
    const detalle = await respuesta.json()
    return route.fulfill({ response: respuesta, json: { ...detalle, archivo: null } })
  })
  try {
    await reenfocar()
    await page.getByText(/El análisis pertenece a otra versión del informe o archivo/).waitFor()
    if (await page.getByRole('img', { name: /Radiografía del estudio/ }).count()) throw new Error('Sigue visible una imagen retirada')
    if (await page.getByRole('heading', { name: 'Hallazgos del modelo experimental' }).count()) throw new Error('Sigue visible el resultado junto a un snapshot incompatible')
  } finally {
    await page.unroute(path)
  }
  return { conflicto_api_real: true, borrador_con_version_original: true, retiro_archivo_simulado: true, resultado_historico_oculto: true }
}
