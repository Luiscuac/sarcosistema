# Auditoría final — SarcoSistema IA

## Dictamen

**SÍ está listo para una demostración universitaria controlada del prototipo, con el guion y limitaciones de este informe. NO está completamente cerrado ni validado para uso clínico.** La integración gráfica y el runtime sin Internet se ejecutaron nuevamente; los errores de extracción y la recuperación genérica siguen presentes y deben mostrarse como limitaciones, no como diagnósticos correctos.

Auditoría de esta sesión: navegador con login real, una inferencia nueva Windows, una inferencia nueva Docker sin salida externa, RAG local nuevo, comprobación de persistencia y de los artefactos históricos de Fase5. **No se repitió el lote de 60 imágenes**; se verificaron sus archivos/resultados y se recalcularon sus AUROC/AP. No hubo reentrenamiento, funcionalidades nuevas ni reestructuración. La única corrección de código fue el aislamiento de una prueba opcional PostgreSQL.

Evidencia resumida: [`auditoria-final-resultados.json`](auditoria-final-resultados.json). Evidencia privada completa: `C:\Users\HP NOTEBOOK\AppData\Local\Temp\opencode\auditoria_final_caa04581\` (sin publicar credenciales). Captura gráfica: `.playwright-mcp/auditoria-final-rayos-x.png`.

## A. Estado de cada fase

| Fase | Estado | Evidencia y alcance |
|---|---|---|
| 1. Repositorio, arquitectura y hardware | Completada | Backend modular FastAPI, frontend React/Vite, PostgreSQL y cola integrada. Python3.12.10, Node24.14.0/npm11.9.0, Ryzen7 5700U,16GB; CPU real y RAM medidas. Importar `app.main` no carga Torch. |
| 2. TorchXRayVision | Completada técnicamente | DenseNet121 preentrenada `densenet121-res224-all`, XRV1.5.7/Torch2.6.0+cpu. Nuevas inferencias desde UI y offline, pesos locales verificados, salida distinta por imagen en el lote histórico. No es modelo entrenado aquí ni precisión clínica validada. |
| 3. RAG local | Completada funcionalmente con alternativa extractiva | PostgreSQL/pgvector0.8.7, `vector(384)`, búsqueda coseno real, MiniLM multilingüe local,2 documentos/215 fragmentos. Cuatro citas nuevas verificadas contra filas, offsets y documentos locales. No existe un LLM radiológico integrado: respuesta extractiva documentada. Calidad limitada por corpus y pregunta fija. |
| 4. Integración Rayos X | **Parcialmente completada** | UI→API→cola→visión→fusión→RAG→revisión funciona; corrección persiste tras recargar sin cambiar informe. Pendientes errores reales de alcance de negación/incertidumbre y consulta RAG no adaptada al caso. No afirmar interpretación radiológica correcta de cualquier informe. |
| 5. Evaluación y offline | Completada como ensayo exploratorio aprobado |300 textos75×4,60 NIH derivados y40 preguntas. Siete archivos crudos históricos y60 imágenes verificados por SHA256; métricas recalculadas. Nueva API offline exit0. NIH tiene etiquetas débiles y posible exposición al entrenamiento; ablación contractual usa scores sintéticos/replay explícitos. No es evaluación externa clínica. |

## B. Pruebas ejecutadas y evidencia

### B1. Recorrido completo desde la interfaz

Se iniciaron PostgreSQL, uvicorn y Vite localmente; no se reutilizó un backend viejo. La asistencia se habilitó **solo en el entorno del proceso**, sin sobrescribir `.env`. El usuario ficticio `medico_demo` ya existía: se verificó su clave local sin imprimirla ni renovarla. Se creó únicamente el estudio demo que aún no existía, mediante el preparador del repositorio, sin sustituir cuentas, pacientes o informes previos.

Pasos ejecutados por Playwright, sin mock de endpoints/modelos:

1. Login en `http://localhost:5173/login` con cuenta médica ficticia.
2. Inicio→Rayos X→`RX-DEMO-IA-001` (estudio32).
3. Radiografía NIH autorizada real512×512 cargada en pantalla.
4. SHA256 de bytes HTTP de la imagen = hash del análisis = `preprocessing.original_sha256` del trabajador.
5. Confirmación explícita de tórax frontal/PA y solicitud real HTTP202.
6. Trabajo nuevo `f4890466-6f3e-4a38-b43d-2c076707f257` completado, con métricas del trabajador y pesos locales.
7. Extracción observada: derrame `negado`, cardiomegalia `incierto`, consolidación `no_mencionado`, correcta **para este informe sintético acotado**.
8. Cuatro referencias recuperadas, desplegadas en la pantalla; cita visible igual al texto de la API. Posteriormente se contrastaron las cuatro contra PostgreSQL y los documentos locales completos.
9. Selección «Corregir propuesta», motivo y texto de corrección ficticios; guardado explícito.
10. Recarga de página y reapertura: versión1 `corregida` y corrección siguen visibles; actor/revisión comprobados en BD. Informe publicado igual al anterior; cero diagnósticos confirmados automáticamente.

Tiempo clic→resultados visibles: **57,432s**. Recursos externos solicitados por el navegador durante la prueba: **0** (se bloquearon destinos no locales). Esto no prueba por sí solo aislamiento de red del backend; ese aislamiento se comprobó separadamente en Docker.

Artefactos privados: `browser-audit.js`, `browser-resultado.json`, `analisis-browser.json`, `memoria-browser.json`, `verificaciones.json`. Script de ejecución gráfica cargado por la herramienta desde `.playwright-mcp/auditoria-final.browser.js`. No se usaron resultados estáticos de una prueba anterior.

### B2. Visión y preprocesamiento

Código revisado: `backend/app/imagenes/infrastructure/vision/{worker,preprocesamiento,servicio,artefactos}.py`.

- Constructor XRV `weights=None` evita descargas; **no significa pesos aleatorios durante inferencia**: a continuación se carga estrictamente el safetensors preentrenado local con `load_state_dict(..., strict=True)`. Hash, versión, etiquetas y puntos operativos se verifican.
- PNG/JPEG de8bits; firma, dimensiones y profundidad original PNG comprobadas antes de inferir. El helper de preprocesamiento valida antes de su propio import de Torch, pero **el trabajador real ya importó Torch y cargó el modelo antes de llamar al helper**; no afirmar rechazo antes de cargar pesos en el recorrido completo.
- Normalización oficial `[0,255]→[-1024,1024]`; promedio de canales RGB; `XRayCenterCrop`, `XRayResizer(224)`, tensor float32 `[1,1,224,224]`; no se modifica el archivo original.
- CPU, `eval()` e `inference_mode()`,4hilos, selección por nombre. Sigmoid/`op_norm` XRV: scores **no calibrados, no probabilidades clínicas**.
- El backend no recibe una nueva subida al pulsar analizar: recibe el ID del estudio y lee el archivo local autorizado. La coincidencia de hash demuestra qué imagen se procesó.
- Nuevas salidas reales coherentes con los pesos: consolidación≈0,312433, derrame≈0,394274, cardiomegalia≈0,621515. Repetir la misma imagen con el mismo modelo puede repetir scores; no implica una simulación.

### B3. RAG, citas y alternativa a Ollama

Código: `infrastructure/rag/{embeddings,repository,servicio}.py`, `application/consultar_rag.py` y `application/analizar_estudio.py`.

- Modelo local: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`; hashes de snapshot, `local_files_only=True`, safetensors y `trust_remote_code=False`.
- SQL ejecutado por el repositorio: `f.embedding <=> CAST(:embedding AS vector)`, filtrado por modelo, orden por distancia y límite; columna real `vector(384)`. No es una lista de citas hardcodeada.
- Documentos: *Chest radiography in adult critical care unit: A pictorial review* (`PMC6958895`) y *Pleural effusion: diagnosis, treatment, and management* (`PMC4753987`), guardados como texto/fragmentos en PostgreSQL y XML local con licencia/procedencia.
- Las cuatro citas del navegador coinciden con el fragmento persistido, documento, rango y SHA256. La pantalla no inventa otra explicación: muestra extractos recuperados y mensajes de seguridad.
- **Limitación importante:** la consulta de integración es fija para las tres categorías. Recuperó secciones sobre ARDS/aspiración, derrame maligno y derrame asociado a absceso amebiano: relacionadas por vocabulario, **no evidencia de que este caso tenga esas causas**. No se probó pertinencia clínica específica del paciente. Integridad de la cita no equivale a relevancia o diagnóstico.

Ollama0.40.14 responde localmente; `ollama list` muestra `qwen2.5:3b` instalado (1,9GB) y `ollama ps` no muestra modelos cargados. **No se ejecutó generación LLM en esta auditoría**: en el punto de control había4.162.297.856bytes libres, menos del margen conservador4GiB. No se retiró ese margen ni se cargó otro modelo simultáneo. La alternativa extractiva radiológica sí se ejecutó y funciona; Ollama no participa en Rayos X. No se afirma que un LLM radiológico generó las explicaciones ni que se probó Ollama offline.

### B4. Pruebas y comandos

Desde `backend/`, usando `.\.venv\Scripts\python.exe -B`:

| Comando/prueba | Resultado nuevo |
|---|---|
| `-m alembic current` y `-m alembic upgrade head` | Cabecera única `20261109_0012`; upgrade ya en head sin DDL pendiente |
| `-m scripts.verificar_esquema_accesos` | Esquema de acceso comprobado |
| `-m scripts.preparar_estudio_imagen_demo --preparar-demo --usuario medico_demo` | Solo nuevo estudio ficticio preparado; no renovación de cuenta |
| `-m pip check` | Sin dependencias rotas |
| `-c "import app.main,sys; print('torch' in sys.modules)"` | Importación correcta; `False` |
| `-m pytest -q -rs --tb=short -p no:cacheprovider` sobre instalación con uvicorn activo | **297 passed,12 skipped en24,26s**, sin fallos; una omisión extra porque el servidor posee el liderazgo de cola |
| Prueba de liderazgo sobre copia aislada sin ejecutor | **1 passed en0,31s**; no se interrumpió el líder del servidor |
| Dos pruebas combinadas RAG→Consultas, antes del arreglo | **1 passed,1 failed**, `Event loop is closed`/`NoneType.send` |
| Mismas dos pruebas después del arreglo | **2 passed en0,82s** |
| Suite completa en copia migrada, `RUN_RAG_DB_TESTS=1` | **299 passed,10 skipped en24,95s**; sin fallos |
| Playwright UI real | Recorrido/corrección/persistencia aprobados, descritos arriba |
| `python -m scripts.verificar_imagenes_offline` en contenedor aislado | Nueva API real **exit0**, sin OOM,4citas, idempotencia, revisión y conflicto409 correctos |
| `ollama --version`, `ollama list`, `ollama ps`, `ollama serve --help` | CLI/servidor local/modelo instalado comprobados; no generación LLM |

Frontend, desde `frontend/`: `npm test`→**27/27**, `npm run lint`→sin errores, `npm run build`→correcto (Vite5.4.21,206módulos,12,48s). No se instalaron dependencias nuevas.

Omisiones finales en copia:1symlink Windows,2harness RAG offline antiguos,1caso POSIX SIGTERM,1prueba visual optativa,3harness visual offline antiguos y2Ollama/Consultas optativas. Se ejecutaron visión/RAG/API offline nuevos, pero no se finge haber repetido todos los escenarios negativos de los harness antiguos. En la instalación con servidor activo se omitieron además RAG opcional por flag y liderazgo; ambas se ejecutaron en copia.

### B5. Prueba nueva sin Internet

Contenedor `sarco-auditoria-offline-caa04581`, imagen de evaluación `sha256:43a643497e1686e985d2e1abf6926aad3cd1bcaa8e310d662f80c8b8d4c2c775`. PostgreSQL temporal `sarco-fase5-db-a3536ff7` con `--network none`; runner `--network container:<ese PostgreSQL>`, sin puertos publicados, raíz de solo lectura,3GiB RAM/swap total y4CPU.

La prueba intenta una conexión real del SO a `1.1.1.1:443` y exige que falle, luego ejecuta autenticación JWT, imagen, cola, modelos, citas, revisión y persistencia local. **Resultado: exit0,44,450s externos, `OOMKilled=false`, informe intacto.** Sin desconectar adaptadores Windows, cambiar firewall, usar servicios externos ni afectar otras aplicaciones. No fue un navegador dentro de esa frontera: la prueba UI y el aislamiento backend se verificaron por separado.

Se compararon hashes de siete archivos de producción del contenedor con los del host: visión, preprocesamiento, embeddings, SQL, fusión, caso de uso y respuesta extractiva coinciden. No se atribuye a una imagen Docker antigua código de producción diferente. La corrección de pruebas de esta auditoría no cambia ese runtime.

Pesos safetensors visuales, snapshot de embeddings y corpus estaban montados localmente en lectura. No se montó el checkpoint pickle visual ni se permitieron descargas runtime. No hay API externa obligatoria para Rayos X. **Fuera de este alcance**, Whisper puede descargar su modelo en el primer uso si no está preparado; no se declara todo el sistema de audio probado offline.

Reproducción completa del entorno aislado: comandos PowerShell en [`fase-5-evaluacion.md`](fase-5-evaluacion.md), sección Offline. No reutilizar credenciales temporales ni ejecutar bootstrap sobre la base habitual.

### B6. Hardware y rendimiento medidos

Equipo: Ryzen7 5700U/8núcleos/16hilos,16.455.806.976bytes RAM físicos, Radeon integrada **no utilizada para inferencia**. Disco libre observado:108.148.793.344bytes (~108,15GB decimales). No se ejecutó estrés prolongado.

| Medición nueva | Resultado | Alcance |
|---|---:|---|
| Backend/reposo al comenzar muestreo |116.269.056bytes (~111MiB) | RSS del árbol de procesos |
| Pico backend+trabajadores |1.016.258.560bytes (~969MiB) |811muestras cada0,15s; no máximo absoluto ni RAM de todo Docker/OS |
| RAM libre mínima host observada |3.422.642.176bytes (~3,19GiB) | Durante el recorrido gráfico |
| Pase de red visual Windows |0,223s | Solo inferencia tensorial |
| Análisis visual completo Windows |17,899s | Proceso, imports, pesos y preprocesamiento incluidos |
| Embedding local para consulta genérica |20,245s | Medición separada, un arranque de trabajador |
| Recuperación PostgreSQL y consultas metadata |0,157s | Incluye conexión/búsqueda e introspección de dimensión/tipo |
| Verificación+respuesta extractiva |0,000585s | No es generación LLM |
| RAG completo separado |20,431s | Corpus, embedding, búsqueda y extractos |
| Clic→resultados visibles |57,432s | Incluye cola, persistencia y polling UI; no sumar mecánicamente mediciones separadas |
| Nueva API offline, desde host |44,450s | Incluye arranque Docker y comprobaciones |
| Visión completa de esa API offline |11,282s | Pase de red0,173s; RSS del trabajador463.314.944bytes |

No se detectó OOM en la nueva prueba. No se midió pico máximo absoluto, concurrencia multiusuario ni tiempo de generación de un LLM. **La laptop es razonable para una demo de un estudio a la vez**, con visión y embeddings secuenciales y sin Whisper/Ollama cargados simultáneamente. Esperar decenas de segundos, no respuesta instantánea. Los2GiB libres configurados para visión son el perfil acotado de las muestras512px previamente medidas; para imágenes arbitrarias conservar el mínimo general4GiB y revisar recursos. La medición no es garantía operativa para otras resoluciones/cargas.

### B7. Auditoría de Fase5

Verificados nuevamente:300JSONL válidos, IDs/textos únicos, etiquetas sintéticas explícitas y75casos por grupo;60archivos NIH derivados224×224 con hashes correctos y pacientes distintos; siete JSON crudos históricos coinciden con sus hashes; AUROC y AP de las tres clases recalculadas con scikit-learn coinciden (tolerancia1e-12).

| Resultado histórico verificado, NO lote nuevo de esta auditoría | Valor |
|---|---:|
| Exactitud objetivo en300textos sintéticos |242/300=80,67%; macro-F1=0,797869 |
| Ambiguos |45/75=60% |
| AUROC consolidación/derrame/cardiomegalia, referencia NLP débil |0,7970 /0,7861 /0,9037 |
| RAG40preguntas: Recall@4 secciones /MRR@10 |0,9167 /0,6019 sobre24respondibles |
| Preguntas respondibles con alguna cita |14/24, no exactitud de respuesta |
| Integridad de citas |41/41; no garantiza pertinencia clínica |
| Precisión/recall de abstención |52,38% /68,75% |
| Comparación300pares con/sin RAG |Scores/fusión iguales300/300; solo añade citas; visión sintética y replay documental explícitos |

No se compararon dos modelos visuales distintos ni una nueva API real con RAG apagado. La ablación **no demuestra mejora diagnóstica ni ahorro de latencia**. NIH derivado tiene etiquetas débiles, selección enriquecida y posible solapamiento con entrenamiento. Algunas métricas no serían definibles sin positivos/negativos; aquí las tres clases tienen ambos, por eso se pudieron calcular. No hay métrica de validación clínica ni diagnóstico sobre los textos sintéticos.

## C. ¿Está listo para una demostración universitaria?

**SÍ**, para demostrar honestamente un prototipo local que calcula scores, extrae términos limitados, recupera citas y exige revisión humana. Se ejecutaron la interfaz y la API aislada, no solo pruebas con dobles. El informe demo elegido evita los errores conocidos y está identificado como ficticio; esos errores se incluyen también como ejemplos de límites.

**No equivale a «todo terminado».** La fase4 sigue parcial. No presentar generación LLM radiológica, interpretación clínica general, precisión diagnóstica, validación externa ni mejora clínica por RAG. La demostración debe explicar la pregunta fija y la diferencia entre una referencia auténtica y una referencia pertinente al caso.

## D. Ejecución después de reiniciar la laptop

### D1. Instalación ya preparada (situación auditada)

1. Abrir Docker Desktop y esperar que el motor esté listo. Conservar esta rama/árbol de trabajo: hay archivos nuevos aún sin commit; cambiar a `main` no equivale a tener esta entrega.
2. PowerShell **terminal1**, desde la raíz real:

```powershell
cd 'C:\Users\HP NOTEBOOK\Downloads\sarcosistema'
docker compose up -d db
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
$env:RADIOLOGY_AI_ENABLED='true'
$env:RADIOLOGY_VISION_MIN_FREE_MIB='2048'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`2048` es **solo el perfil del demo NIH512px**; para otra carga usar4096. Es obligatorio habilitar IA en la terminal que inicia uvicorn: `.env` permanece deshabilitado por defecto. No cambiar `DATABASE_URL` local a `db`; eso corresponde a contenedores. No reemplazar `.env` ni claves existentes.

3. PowerShell **terminal2**:

```powershell
cd 'C:\Users\HP NOTEBOOK\Downloads\sarcosistema\frontend'
npm run dev -- --host localhost --strictPort
```

4. Abrir `http://localhost:5173`. Backend: `http://localhost:8000/docs`; salud `http://localhost:8000/health` y `/health/db`. Usar `localhost:5173`, no cambiarlo por127.0.0.1 (CORS). Mantener ambas terminales abiertas. Si el puerto está ocupado, identificar el proceso antes de detenerlo; no iniciar otra instancia en un puerto diferente. El worker de cola lo inicia el lifespan de FastAPI con IA habilitada: no hay Celery, Redis ni servicio adicional que ejecutar.

5. **Ollama es opcional y no se necesita para Rayos X.** Si se quiere comprobar su disponibilidad, `ollama list` y `ollama ps`. Si no está iniciado, abrir otra terminal y ejecutar `ollama serve` (puerto local11434; no iniciar un segundo servidor si ya responde). `qwen2.5:3b` ya está descargado. No cargarlo durante el análisis visual/embeddings si falta margen RAM. No se usa `ollama pull` en el arranque diario ni se promete una generación no comprobada.

6. Cuenta demo: `medico_demo`; usar la clave privada existente. Su ruta se conserva en el preparador/config local de la auditoría; no se publica en este informe. No regenerar ni renovar la contraseña de una cuenta existente. No ejecutar los preparadores de datos en cada inicio.

No se reinició físicamente Windows durante esta auditoría: se probaron los comandos/servicios sobre esta sesión, no se afirma haber probado el ciclo completo de reboot. No usar las bases temporales tmpfs de evaluación como la instalación persistente.

### D2. Preparación inicial si faltan dependencias o artefactos

Solo en una instalación nueva y **con Internet durante preparación**: seguir los pasos no destructivos del README para `.venv`, `.env` y `npm ci`. Desde `backend/`, los archivos verificados son:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia-cpu.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia.txt -r requirements-rag.txt
.\.venv\Scripts\python.exe -m scripts.preparar_modelos_radiologia --descargar
.\.venv\Scripts\python.exe -m scripts.preparar_muestras_radiologia --descargar
.\.venv\Scripts\python.exe -m scripts.preparar_rag_torax --descargar
.\.venv\Scripts\python.exe -m scripts.consultar_rag_torax --indexar
```

Las rutas/flags existen en el repositorio; **no se reinstalaron ni se volvieron a descargar aquí**, pues ya estaban preparados. El preparador de muestras aborta si ya existe manifiesto: conservarlo. Bootstrap `database/schema.sql` solo lo inicializa Compose al crear una base vacía; no repetirlo sobre datos existentes. Usar `.venv` existente, no recrearlo después de cada reinicio.

En una base realmente nueva, preparar una sola vez la cuenta ficticia con `scripts.preparar_medico_demo` y después `scripts.preparar_estudio_imagen_demo --preparar-demo --usuario medico_demo`; ambos abortan ante registros reservados existentes. No ejecutar sobre cuentas ajenas ni inventar una contraseña sembrada.

## E. Guion reproducible de demostración

**Imagen disponible:** `backend/.datasets/radiologia/NIH-RX-001.png` (NIH `00000001_000.png`, fixture autorizado XRV,512×512,PA; etiqueta NIH débil cardiomegalia). El preparador copia exactamente sus bytes a `.storage/radiologia/` con nombre único y hash; la UI la encuentra mediante el estudio, no por una URL externa.

**Informe ya guardado para `RX-DEMO-IA-001`:**

> SIMULACIÓN DE INTEGRACIÓN: este texto ficticio no es el informe auténtico de la radiografía NIH adjunta. No se observa derrame pleural. Posible cardiomegalia. Revisar las propuestas experimentales, no usarlas como diagnóstico.

Es compatible con el **guion técnico**, no un informe adjudicado de esta imagen. No llamarlo caso clínico real emparejado.

1. Iniciar según D y entrar como médico. Inicio→Rayos X→`RX-DEMO-IA-001`→Ver estudio.
2. Mostrar imagen local e informe publicado de solo lectura; señalar la etiqueta de simulación y la procedencia NIH.
3. Confirmar tórax frontal, elegir PA y pulsar «Analizar con IA local». Esperar hasta aproximadamente un minuto; no cerrar el backend.
4. Mostrar scores y advertencia: cardiomegalia≈0,622 no significa62,2% de certeza. Un score bajo no descarta enfermedad.
5. Mostrar extracción: derrame negado; cardiomegalia incierta; consolidación no mencionada. Explicar que la IA no decide entre informe y score.
6. Abrir «Evidencia documental local»: título, sección, cita, origen, rango y SHA256. Explicar que es recuperación de fuentes existentes, **no una conclusión médica generada por Ollama**. Mostrar también que algunas referencias son genéricas y no describen al paciente.
7. Seleccionar «Corregir propuesta», escribir motivo y una corrección **ficticia**, por ejemplo «Mantener incertidumbre del informe; los scores no confirman diagnósticos». Guardar explícitamente.
8. Recargar y reabrir: la nueva versión/actor/motivo/corrección persisten; el informe permanece sin cambios. La auditoría ya creó una versión1 de un análisis; otro análisis tendrá su propio historial. No prometer que cualquier repetición mostrará exactamente versión1.
9. Como límites de investigación, mostrar en el informe los tres ejemplos sintéticos que el extractor interpreta mal y las métricas de Fase5. No introducir esos ejemplos como hallazgos auténticos de la imagen.

## F. Pendientes por prioridad

### Críticos — impiden la demostración

**No se detectó un bloqueo crítico pendiente para el guion controlado después de preparar/habilitar servicios.** Condiciones de bloqueo reproducibles: IA deshabilitada, pesos/corpus ausentes, BD detenida o RAM insuficiente. Se mantienen las guardas: no silenciar esos errores ni retirarlas para forzar el demo. La ausencia de una entrega completa en Git impide reproducirla simplemente clonando el último commit; conservar el árbol actual hasta que el usuario autorice versionarlo.

### Importantes — afectan funcionalidad o interpretación

1. **Negación/incertidumbre incorrectas** (`application/fusionar_hallazgos.py`): «No hay derrame pleural y hay cardiomegalia» niega incorrectamente cardiomegalia; «Derrame pleural no evidente» y «Consolidación?» se interpretan como descritos. Reproducidos de nuevo, no corregidos porque no bloquean el guion y cambiar semántica requeriría diseño/validación aparte.
2. **RAG genérico, no adaptado al informe** (`application/analizar_estudio.py:31`): fuentes auténticas pueden ser poco pertinentes al caso. No hay síntesis clínica ni explicación razonada específica del paciente. Mejorar relevancia requiere un cambio funcional, fuera de esta auditoría.
3. Corpus pequeño, referencias débiles/no independientes, textos sin adjudicación experta; no hay evidencia de validez clínica. Entrenamiento nuevo no justificado.
4. Muchos archivos modificados/nuevos sin commit: entrega no consolidada. No se hizo commit/push sin autorización; no se cambió de rama.
5. Defaults y entorno importan: `.env` mantiene IA apagada; el perfil2GiB se limita al demo; no inferir capacidad multiusuario ni correr todos los modelos simultáneamente.

### Menores — no bloquean el guion

- `app/imagenes/storage.py` conserva2métodos `NotImplementedError`, sin consumidores en el flujo real. El lector actual es `infrastructure/archivos.py`; no hay subida general de imágenes desde esta pantalla. No se eliminó el archivo.
- `shared/exceptions.py` mantiene un TODO de observabilidad; no se conectó Sentry ni se añadieron destinos externos. Los `pass` de excepciones/Base/schema y capturas controladas no son inferencia simulada.
- Favicon404 y aviso de migración futura React Router v7 en modo desarrollo; no afectan UI/modelos. No se modificó el diseño.
- El trabajador carga modelo antes de validar todos los detalles de la imagen; una fuente incompatible puede pagar ese coste aunque termine rechazada antes de la inferencia. Las pruebas aisladas del helper no demuestran un rechazo anterior a la carga en el flujo completo.
- Documentación histórica/AGENTS puede conservar conteos previos; README y guía de integración se actualizaron a cabecera0012. Alembic y este informe son la evidencia actual, no un conteo de otra sesión.

### Error pequeño corregido durante la auditoría

La prueba optativa `app/imagenes/tests/test_rag_repository.py` usaba el engine global y dejaba conexiones asyncpg para otro event loop. Primero se reprodujo el fallo combinado RAG→Consultas; luego se cambió **solo esa prueba** a engine propio con `NullPool`, rollback y `dispose` en `finally`. Reproductor pasó2/2 y suite completa con RAG299/10. No se cambió la conexión/transacción de producción ni se borraron datos.

Revisión independiente final del informe, evidencia pública y arreglo de prueba: sin hallazgos importantes adicionales. Se corrigió una sobreafirmación documental menor sobre el orden de validación/carga de Torch, sin cambiar el runtime.

## Límites del dictamen

No se certifican seguridad/privacidad institucional, validez médica, precisión en pacientes reales, entrenamiento independiente, DICOM/equipos, concurrencia sostenida ni generación LLM radiológica. El informe permite presentar una demostración académica real y honesta, no anunciar un sistema médico terminado.
