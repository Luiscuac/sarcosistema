// Ejecutable con browser_run_code_unsafe(filename=...). Solo fixtures ficticios;
// comprueba componentes/rutas reales con API controlada, SIN persistir consultas.
async (page) => {
  const fallos = []
  let modo = 'normal'
  let liberarRespuesta
  await page.unroute('http://localhost:8000/**')
  await page.addInitScript(() => {
    window.confirm = () => true
    window.addEventListener('beforeunload', e => e.stopImmediatePropagation(), true)
  })
  await page.route('http://localhost:8000/**', async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/accesos/yo') return route.fulfill({ json: { id: 7, identificador_acceso: 'medico_ficticio', rol: 'medico' } })
    if (path === '/consultas/extraer-datos-clinicos') {
      if (modo === 'error') return route.fulfill({ status: 503, json: { detail: 'Error ficticio de proveedor' } })
      if (modo === 'demora') await new Promise(resolve => { liberarRespuesta = resolve })
      return route.fulfill({ json: {
      propuesta_id: '11111111-1111-4111-8111-111111111111', modelo: 'qwen2.5:3b', bloqueada: false,
      requiere_revision: true, advertencias: [], campos_extraidos: [{ campo: 'sintomas', valor: 'Tos', evidencia: 'Tos', ambiguo: false }],
      } }).catch(() => {})
    }
    const match = path.match(/^\/consultas\/pacientes\/(\d+)$/)
    if (match) return route.fulfill({ json: {
      id: Number(match[1]), nombre_completo: `Paciente ficticio ${match[1]}`, codigo_paciente: `PAC-TEST-${match[1]}`,
      fecha_nacimiento: '1990-01-01', sexo: 'F', estado: 'activo',
    } })
    return route.fulfill({ json: { items: [], total: 0, pagina: 1, limite: 20 } })
  })
  await page.goto('http://localhost:5173/login')
  await page.evaluate(() => sessionStorage.setItem('token', 'token-ficticio-solo-test'))
  await page.goto('http://localhost:5173/consultas/pacientes/1/nueva')
  await page.getByRole('heading', { name: 'Nueva consulta' }).waitFor()
  await page.getByLabel(/^Motivo de consulta/).fill('Manual del paciente uno')
  await page.evaluate(async () => {
    let router
    function buscar(fiber) {
      if (!fiber || router) return
      if (fiber.memoizedProps?.router?.navigate) { router = fiber.memoizedProps.router; return }
      buscar(fiber.child); buscar(fiber.sibling)
    }
    const root = document.getElementById('root')
    buscar(root[Object.keys(root).find(key => key.startsWith('__reactContainer'))])
    if (!router) throw new Error('No se encontró RouterProvider para prueba de navegación')
    await router.navigate('/consultas/pacientes/2/nueva')
  })
  await page.getByText('Paciente ficticio 2', { exact: true }).waitFor()
  if (await page.getByLabel(/^Motivo de consulta/).inputValue()) fallos.push('cambio de paciente conserva valores clínicos')

  await page.locator('form label').filter({ hasText: /^Síntomas/ }).locator('textarea').fill('Manual')
  await page.getByText('Revisar texto y volver a procesar', { exact: true }).click()
  await page.getByLabel('Texto para análisis (no cambia el original)').fill('Síntomas: Tos.')
  await page.getByRole('button', { name: 'Analizar texto', exact: true }).click()
  await page.getByRole('button', { name: 'Aceptar este campo', exact: true }).click()
  await page.locator('form label').filter({ hasText: /^Síntomas/ }).locator('textarea').fill('Cambio manual')
  await page.locator('form label').filter({ hasText: /^Síntomas/ }).locator('textarea').fill('Tos')
  await page.getByRole('button', { name: 'Deshacer (sin borrar correcciones posteriores)' }).click()
  if (await page.locator('form label').filter({ hasText: /^Síntomas/ }).locator('textarea').inputValue() !== 'Tos') fallos.push('deshacer altera una decisión manual posterior')

  modo = 'demora'
  await page.getByRole('button', { name: 'Analizar texto', exact: true }).click()
  await page.getByText('Analizando información clínica…', { exact: true }).waitFor()
  await page.getByRole('button', { name: 'Cancelar propuestas y continuar manualmente' }).click()
  liberarRespuesta?.()
  await page.getByText('Sin grabación activa', { exact: true }).waitFor()
  if (await page.getByRole('button', { name: 'Aceptar este campo', exact: true }).count()) fallos.push('respuesta cancelada reaparece como propuesta')
  modo = 'error'
  await page.getByRole('button', { name: 'Analizar texto', exact: true }).click()
  await page.getByText('Error de procesamiento', { exact: true }).waitFor()
  await page.getByLabel(/^Motivo de consulta/).fill('Control manual ficticio')
  await page.getByLabel(/^Diagnóstico principal/).fill('Evaluación manual ficticia')
  if (await page.getByRole('button', { name: 'Finalizar y guardar consulta' }).isDisabled()) fallos.push('fallo de IA impide guardar manualmente')

  await page.goto('http://localhost:5173/consultas/pacientes/1/nueva')
  await page.getByRole('heading', { name: 'Nueva consulta' }).waitFor()
  await page.evaluate(() => {
    window.__microfonoPrueba = { inicios: 0, paradas: 0 }
    navigator.mediaDevices.getUserMedia = () => new Promise(resolve => {
      window.__resolverMicrofono = () => {
        const track = { stop: () => window.__microfonoPrueba.paradas++, getSettings: () => ({}) }
        resolve({ getTracks: () => [track], getAudioTracks: () => [track] })
      }
    })
    window.MediaRecorder = class {
      static isTypeSupported() { return true }
      constructor() { this.state = 'inactive' }
      start() { this.state = 'recording'; window.__microfonoPrueba.inicios++ }
      stop() { this.state = 'inactive' }
    }
  })
  await page.getByRole('checkbox').check()
  await page.getByRole('button', { name: 'Iniciar grabación', exact: true }).click()
  await page.getByRole('link', { name: 'Inicio', exact: true }).click()
  await page.getByRole('heading', { name: 'Bienvenido a SarcoSistema' }).waitFor()
  const mic = await page.evaluate(async () => {
    window.__resolverMicrofono()
    await new Promise(resolve => setTimeout(resolve, 50))
    return window.__microfonoPrueba
  })
  if (mic.inicios !== 0 || mic.paradas !== 1) fallos.push('micrófono pendiente inicia tras salir o no libera pistas')
  await page.unroute('http://localhost:8000/**')
  await page.evaluate(() => sessionStorage.removeItem('token'))
  if (fallos.length) throw new Error(fallos.join('; '))
  return { pruebas: 5, resultado: 'PASS', persistencia: 'ninguna; API ficticia controlada' }
}
