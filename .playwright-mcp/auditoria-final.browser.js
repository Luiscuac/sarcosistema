async (page) => {
  const proceso = page.constructor.constructor('return process')()
  const fs = proceso.getBuiltinModule('fs')
  const crypto = proceso.getBuiltinModule('crypto')
  const raiz = fs.readFileSync('C:/Users/HP NOTEBOOK/AppData/Local/Temp/opencode/auditoria_final_actual.txt','utf8').trim()
  const config = JSON.parse(fs.readFileSync(raiz+'/browser-config.json','utf8'))
  const externos = []
  await page.route('**/*', route => {
    const host = new URL(route.request().url()).hostname
    if (!['localhost','127.0.0.1'].includes(host)) { externos.push(host); return route.abort() }
    return route.continue()
  })
  await page.goto(config.frontend+'/login')
  await page.getByLabel('Usuario *',{exact:true}).fill(config.usuario)
  await page.getByLabel('Contraseña *',{exact:true}).fill(fs.readFileSync(config.key_path,'utf8').trim())
  await page.getByRole('button',{name:'Ingresar',exact:true}).click()
  await page.getByRole('link',{name:'Entrar a Rayos X'}).click()
  await page.getByRole('heading',{name:'Estudios radiológicos',exact:true}).waitFor()
  const imagenPromise = page.waitForResponse(r=> /\/imagenes\/estudios\/\d+\/archivos\/\d+$/.test(r.url()) && r.status()===200)
  await page.getByRole('row').filter({hasText:'RX-DEMO-IA-001'}).getByRole('button',{name:'Ver estudio'}).click()
  await page.getByText(/SIMULACIÓN DE INTEGRACIÓN/).first().waitFor()
  const imagenHttp = await imagenPromise
  const hashImagen = crypto.createHash('sha256').update(await imagenHttp.body()).digest('hex')
  const imagen = page.getByRole('img',{name:/Radiografía del estudio/})
  await imagen.waitFor()
  if (!await imagen.evaluate(img=>img.complete && img.naturalWidth===512)) throw Error('Radiografia real no cargada')
  await page.getByLabel('Confirmo que es una radiografía de tórax frontal').check()
  const iniciadaPromise = page.waitForResponse(r=>r.url().includes('/analisis')&&r.request().method()==='POST')
  const inicio = Date.now()
  await page.getByRole('button',{name:'Analizar con IA local',exact:true}).click()
  const http = await iniciadaPromise
  if(http.status()!==202) throw Error('Analisis HTTP '+http.status())
  const inicioJob = await http.json()
  const authorization = http.request().headers()['authorization']
  await page.waitForFunction(()=>document.body.innerText.includes('Hallazgos del modelo experimental') ||
    [...document.querySelectorAll('[role=alert]')].some(e=>/Memoria|falló|máximo|Faltan pesos|Otro modelo|integridad/.test(e.textContent)),null,{timeout:240000})
  if (!await page.getByRole('heading',{name:'Hallazgos del modelo experimental'}).count()) throw Error('Modelo real no completo')
  const totalSeconds = (Date.now()-inicio)/1000
  const get = async url => { const r=await page.request.get(url,{headers:{Authorization:authorization}}); if(r.status()!==200)throw Error('GET '+r.status());return r.json() }
  const url=config.backend+'/imagenes/analisis/'+inicioJob.id
  const analisis=await get(url)
  if(analisis.estado!=='completado'||analisis.archivo_sha256!==hashImagen||analisis.resultado.vision.preprocessing.original_sha256!==hashImagen)throw Error('No coincide la imagen procesada')
  if(analisis.resultado.fusion.hallazgos_confirmados.length)throw Error('Diagnostico confirmado automaticamente')
  const fuentes=await get(url+'/fuentes')
  if(!fuentes.fuentes.length)throw Error('Sin evidencia RAG')
  const detalleUrl=config.backend+'/imagenes/estudios/'+analisis.estudio_id
  const antes=await get(detalleUrl)
  for(const hallazgo of analisis.resultado.vision.findings) {
    if(!(await page.locator('body').innerText()).includes(hallazgo.score.toFixed(3)))throw Error('Score no mostrado')
  }
  const detalles = page.locator('section[aria-label="Detalle del estudio"] details')
  await detalles.first().locator('summary').click()
  const citaUI=await detalles.first().locator('blockquote').textContent()
  if(citaUI!==fuentes.fuentes[0].cita)throw Error('Cita UI diferente de API')
  await page.getByLabel('Decisión',{exact:true}).selectOption('corregida')
  await page.getByLabel('Motivo',{exact:true}).fill('Auditoría FICTICIA: revisar explícitamente la propuesta experimental.')
  const correccion='CORRECCIÓN SINTÉTICA DE AUDITORÍA: conservar la incertidumbre del informe; los scores y citas no confirman diagnósticos.'
  await page.getByLabel('Corrección de la propuesta',{exact:true}).fill(correccion)
  await page.getByRole('button',{name:'Guardar revisión explícita'}).click()
  await page.getByText('Revisión guardada; el informe clínico permanece sin cambios.',{exact:true}).waitFor()
  await page.reload()
  await page.getByRole('row').filter({hasText:'RX-DEMO-IA-001'}).getByRole('button',{name:'Ver estudio'}).click()
  await page.getByText('Versión 1: corregida',{exact:false}).waitFor()
  await page.getByText(correccion,{exact:true}).waitFor()
  const despues=await get(detalleUrl)
  const revisado=await get(url)
  if(antes.informe_texto!==despues.informe_texto || revisado.version_revision!==1)throw Error('Persistencia/revision incompatible')
  if(externos.length)throw Error('Recursos externos intentados')
  fs.writeFileSync(raiz+'/analisis-browser.json',JSON.stringify(revisado,null,2))
  const resultado={browser_real:true,login_real:true,imagen_correcta_sha256:true,visual_real:true,
    fuentes_ui_iguales_api:true,numero_citas:fuentes.fuentes.length,correccion_persistida_tras_reload:true,
    informe_publicado_intacto:true,diagnosticos_automaticos:0,recursos_externos_browser:externos.length,
    total_seconds:totalSeconds,analisis_id:inicioJob.id,estudio_id:analisis.estudio_id,
    vision_metrics:analisis.resultado.vision.metrics,extraction:analisis.resultado.fusion.informe}
  fs.writeFileSync(raiz+'/browser-resultado.json',JSON.stringify(resultado,null,2))
  fs.writeFileSync(raiz+'/medicion.stop','fin')
  return resultado
}
