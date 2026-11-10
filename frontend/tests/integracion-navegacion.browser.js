// API y PostgreSQL reales, cuentas exclusivamente ficticias en integration_suite.
// Config privada fuera de Git; no devolver claves, JWT ni contenido clínico.
async (page) => {
  const proceso = page.constructor.constructor('return process')()
  const fs = proceso.getBuiltinModule('fs')
  const path = proceso.getBuiltinModule('path')
  const config = JSON.parse(fs.readFileSync(path.join(proceso.env.LOCALAPPDATA, 'Temp', 'opencode', 'sarco-integracion-browser-private.json'), 'utf8').replace(/^\uFEFF/, ''))
  const fallos = []
  const externos = []
  page.on('pageerror', error => fallos.push(error.name))
  await page.route('**/*', route => {
    if (!['localhost', '127.0.0.1'].includes(new URL(route.request().url()).hostname)) {
      externos.push(true)
      return route.abort()
    }
    return route.continue()
  })
  async function entrar(rol) {
    await page.goto(config.frontend + '/login')
    await page.getByLabel('Usuario *', { exact: true }).fill(config.usuarios[rol])
    await page.getByLabel('Contraseña *', { exact: true }).fill(config.clave)
    await page.getByRole('button', { name: 'Ingresar', exact: true }).click()
  }
  await entrar('medico')
  await page.getByRole('link', { name: 'Entrar a Rayos X', exact: true }).click()
  await page.getByRole('heading', { name: 'Estudios radiológicos', exact: true }).waitFor()
  if (!page.url().endsWith('/imagenes/rayos-x')) throw new Error('Destino de Rayos X incorrecto')
  await page.getByRole('row').filter({ hasText: 'RX-DEMO-IA-001' }).getByRole('button', { name: 'Ver estudio' }).click()
  const imagen = page.getByRole('img', { name: /Radiografía del estudio/ })
  await imagen.waitFor()
  await imagen.evaluate(img => img.complete ? Promise.resolve() : new Promise((ok, fail) => { img.onload = ok; img.onerror = fail }))
  if (!await imagen.evaluate(img => img.naturalWidth > 0)) throw new Error('Archivo radiológico no cargado')
  await page.getByRole('link', { name: 'Consulta médica', exact: true }).click()
  await page.waitForURL('**/consultas')
  // Preparar una solicitud por HTTP real con la sesión médica recién obtenida.
  const solicitud = await page.evaluate(async config => {
    const headers = { Authorization: `Bearer ${sessionStorage.getItem('token')}`, 'Content-Type': 'application/json' }
    const catalogo = await (await fetch(config.api + '/consultas/catalogo-imagenes', { headers })).json()
    const eco = catalogo.find(e => e.codigo === 'ECO_ABDOMINAL')
    const r = await fetch(config.api + '/consultas/estudios-imagen', { method: 'POST', headers,
      body: JSON.stringify({ paciente_id: config.paciente, tipo_estudio_ids: [eco.id], medico_solicitante_nombre: 'Profesional FICTICIO', clave_idempotencia: crypto.randomUUID() }) })
    return r.status
  }, config)
  if (solicitud !== 201) throw new Error('La solicitud real de Ecografía falló')
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click()
  await entrar('imagenes')
  await page.getByRole('link', { name: 'Entrar a radiología (ecografías)', exact: true }).click()
  await page.getByRole('heading', { name: 'Bandeja de estudios', exact: true }).waitFor()
  await page.getByRole('row').filter({ hasText: 'Ecografia abdominal' }).first().getByRole('button', { name: 'Atender', exact: true }).click()
  await page.getByRole('button', { name: 'Guardar borrador', exact: true }).waitFor()
  await page.getByRole('button', { name: 'Cerrar sesión', exact: true }).click()
  await entrar('laboratorio')
  await page.getByRole('heading', { name: 'Solicitudes de laboratorio', exact: true }).waitFor()
  await page.getByRole('button', { name: '+ Nueva solicitud', exact: true }).click()
  await page.getByRole('heading', { name: /Nueva solicitud/ }).waitFor()
  if (fallos.length || externos.length) throw new Error('Error de renderizado o recurso externo')
  return { login_real_tres_roles: true, rayos_x_imagen_real: true, consulta_medica: true,
    ecografia_solicitud_y_bandeja_real: true, laboratorio_formulario: true,
    errores_javascript: fallos.length, recursos_externos: externos.length,
    inferencia_en_navegador: false }
}
