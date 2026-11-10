// Prueba REAL con API/modelos locales. Config fuera de Git; no imprimir claves/JWT.
// Ejecutar mediante browser_run_code_unsafe(filename=...). Solo datos ficticios.
async (page) => {
  const proceso = page.constructor.constructor('return process')()
  const fs = proceso.getBuiltinModule('fs')
  const config = JSON.parse(fs.readFileSync('backend/.radiologia-resultados/integracion-browser-config.json', 'utf8'))
  const externos = []
  await page.route('**/*', route => {
    const url = new URL(route.request().url())
    if (!['localhost', '127.0.0.1'].includes(url.hostname)) {
      externos.push(url.hostname)
      return route.abort()
    }
    return route.continue()
  })
  await page.goto(`${config.frontend}/login`)
  await page.getByLabel('Usuario *', { exact: true }).fill(config.usuario)
  await page.getByLabel('Contraseña *', { exact: true }).fill(fs.readFileSync(config.key_path, 'utf8').trim())
  await page.getByRole('button', { name: 'Ingresar', exact: true }).click()
  await page.getByRole('link', { name: 'Entrar a Rayos X' }).click()
  await page.getByRole('heading', { name: 'Estudios radiológicos', exact: true }).waitFor()
  const fila = page.getByRole('row').filter({ hasText: 'RX-DEMO-IA-001' })
  await fila.getByRole('button', { name: 'Ver estudio' }).click()
  await page.getByText(/SIMULACIÓN DE INTEGRACIÓN/).first().waitFor()
  const imagen = page.getByRole('img', { name: /Radiografía del estudio/ })
  await imagen.waitFor()
  if (!await imagen.evaluate(img => img.complete && img.naturalWidth > 0)) throw new Error('No se cargó la radiografía real')
  await page.getByLabel('Confirmo que es una radiografía de tórax frontal').check()
  const respuesta = page.waitForResponse(r => r.url().includes('/analisis') && r.request().method() === 'POST')
  await page.getByRole('button', { name: 'Analizar con IA local' }).click()
  const http = await respuesta
  if (http.status() !== 202) throw new Error(`No se inició el análisis: HTTP ${http.status()}`)
  const inicio = await http.json()
  await page.waitForFunction(() => document.body.innerText.includes('Hallazgos del modelo experimental') ||
    [...document.querySelectorAll('[role=alert]')].some(e => /Memoria|falló|máximo|Faltan pesos|Otro modelo|integridad/.test(e.textContent)), null, { timeout: 240000 })
  if (!await page.getByRole('heading', { name: 'Hallazgos del modelo experimental' }).count()) throw new Error('El modelo real no completó; revisar aviso de recursos o preparación')
  await page.getByRole('heading', { name: 'Evidencia documental local' }).waitFor()
  await page.getByLabel('Decisión', { exact: true }).selectOption('rechazada')
  await page.getByLabel('Motivo', { exact: true }).fill('Prueba FICTICIA de revisión explícita: no usar como diagnóstico.')
  await page.getByRole('button', { name: 'Guardar revisión explícita' }).click()
  await page.getByText('Revisión guardada; el informe clínico permanece sin cambios.', { exact: true }).waitFor()
  await page.reload()
  await page.getByRole('row').filter({ hasText: 'RX-DEMO-IA-001' }).getByRole('button', { name: 'Ver estudio' }).click()
  await page.getByText(/Versión 1: rechazada/).waitFor()
  if (externos.length) throw new Error('La interfaz intentó usar recursos externos')
  return { api_real: true, modelos_reales: true, imagen_local: true, revision_persistida_tras_recargar: true,
    analisis_id: inicio.id, recursos_externos: externos.length }
}
