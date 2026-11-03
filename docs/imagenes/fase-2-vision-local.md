# Fase 2 — TorchXRayVision local en CPU

Preparación y verificación: 02–03/11/2026.

Alcance: servicio visual y CLI dentro de `backend/app/imagenes/`; **sin endpoints clínicos, frontend, RAG, LLM, embeddings, entrenamiento ni migraciones**. La integración de estudios/revisión médica permanece para fases posteriores.

## Instalación y preparación (único momento con descargas)

Desde `backend/`, con Python 3.12 y RAM/disco revisados:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia-cpu.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia.txt
.\.venv\Scripts\python.exe -m scripts.preparar_modelos_radiologia --descargar
.\.venv\Scripts\python.exe -m scripts.preparar_muestras_radiologia --descargar
```

El primer archivo usa el índice oficial CPU de PyTorch. Pares comprobados en Windows: **torch 2.6.0+cpu**, **torchvision 0.21.0+cpu**, **TorchXRayVision 1.5.7**. No se instalaron CUDA, modelos de texto ni reconocimiento de voz nuevos. Las dependencias son optativas: los flujos manuales no necesitan importarlas ni cargar el modelo.

El modelo es DenseNet-121 `densenet121-res224-all` (18 etiquetas entrenadas), cuyo checkpoint oficial ocupa 28.382.008 bytes. El script conserva:

- Checkpoint oficial y recibo de procedencia/SHA-256, en `backend/.models/radiologia/`.
- Conversión **safetensors** local, sin deserialización pickle durante inferencia.
- `manifest.json` con ID/versión, etiquetas, preprocesamiento, puntos operativos, formato de puntuaciones y hashes.
- Comprobación de equivalencia entre carga oficial y conversión (control tensorial, no un resultado médico). En la preparación realizada, error absoluto máximo **0,0**.

La carga del checkpoint original de confianza se permite **solo en preparación**. No aceptar pesos subidos por usuarios. Un checkpoint existente sin recibo de procedencia se rechaza; no se sobrescribe silenciosamente. Un manifest existente se verifica, sin descargar de nuevo. Ante archivos de preparación incompletos/incompatibles, revisar los archivos concretos antes de repetir; no borrar carpetas generales ni datos clínicos.

Los artefactos, muestras y resultados de ejecución se excluyen de Git. `.dockerignore` también evita enviar `.env`, `.venv`, modelos y datos al contexto de construcción.

## Muestras y permiso de uso

Se prepararon únicamente **dos radiografías NIH desidentificadas**, distribuidas como fixtures por TorchXRayVision, fijando el commit `17726dd8f5e756eec3e5ae958281a289b05b1dae`:

| Muestra local | Imagen de origen | Vista de metadatos | Etiqueta NIH débil |
|---|---|---|---|
| `NIH-RX-001.png` | `00000001_000.png` | PA | Cardiomegaly |
| `NIH-RX-002.png` | `00027426_000.png` | PA | No Finding |

Son PNG de 512×512 de la distribución XRV; se conserva exactamente el archivo descargado, no se afirma que sea el original NIH a resolución completa. `backend/.datasets/radiologia/muestras.json` conserva URL, commit, hash, atribución, vista y clase de etiqueta. La revisión visual no observó identificadores personales evidentes (no sustituye una certificación institucional de desidentificación). No se asignaron pacientes del hospital ni informes inventados.

Permiso verificado en la documentación de Google Cloud sobre la distribución NIH: **sin restricciones de uso de imágenes, con atribución**, enlace al distribuidor y cita del artículo. Se descartó la alternativa Wikimedia al devolver 403 en el transporte local; no se sorteó autenticación ni se descargó un dataset completo.

**Proveedor:** NIH Clinical Center. **Distribuidor original:** https://nihcc.app.box.com/v/ChestXray-NIHCC

**Cita requerida:** Xiaosong Wang, Yifan Peng, Le Lu, Zhiyong Lu, Mohammadhadi Bagheri, Ronald Summers. *ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks on Weakly-Supervised Classification and Localization of Common Thorax Diseases*. IEEE CVPR, 3462–3471, 2017.

**Referencia de permisos:** https://cloud.google.com/healthcare-api/docs/resources/public-datasets/nih-chest#license_and_attribution

No son etiquetas de expertos adjudicadas ni una muestra independiente: el modelo `all` se entrenó, entre otros, con datos NIH y puede haber visto estas imágenes. No usar estos ejemplos para estimar precisión clínica, sensibilidad o especificidad.

## Ejecución local sin descargas

Desde `backend/`, confirmar que la imagen seleccionada es un tórax frontal. Esa confirmación es del operador, **no** una detección automática de modalidad:

```powershell
.\.venv\Scripts\python.exe -m scripts.analizar_radiografia .datasets/radiologia/NIH-RX-001.png --confirmar-torax-frontal --proyeccion PA
```

Para repetir la evaluación acotada realizada sobre muestras 512×512:

```powershell
.\.venv\Scripts\python.exe -m scripts.analizar_radiografia .datasets/radiologia/NIH-RX-001.png --confirmar-torax-frontal --proyeccion PA --repeticiones 3 --min-free-mib 2048
.\.venv\Scripts\python.exe -m scripts.analizar_radiografia .datasets/radiologia/NIH-RX-002.png --confirmar-torax-frontal --proyeccion PA --repeticiones 3 --min-free-mib 2048
```

El mínimo general es **4 GiB libres**. La primera prueba pasó con 4,58 GiB libres; después bajó la memoria y se rechazó una ejecución por recursos insuficientes. Tras medir ~400 MiB RSS reales del trabajador, se usó explícitamente el perfil de **2 GiB** para estas muestras pequeñas, manteniendo margen y sin otros modelos cargados. No se eliminó el control ni se apagaron procesos del usuario. Si la RAM libre cae por debajo del perfil, se devuelve `RecursosInsuficientes`, no se fuerza la inferencia. No extrapolar este perfil a imágenes o cargas mayores sin medirlas.

El puerto reutilizable es `VisionTorax`; `AnalizarTorax` delega a `AnalizadorTorax`. Este valida artefactos y recursos y toma un lock entre procesos. Crea un trabajador CPU efímero por análisis, con hasta tres repeticiones de evaluación, timeout configurable (120 s predeterminado) y terminación del hijo al vencer/cancelar. No quedan modelos persistentes en el servidor FastAPI; tampoco se cambió su router.

En esta fase el lock coordina las inferencias **visuales** locales; todavía no es un planificador compartido con Whisper/Ollama ni entre Windows y contenedores distintos. Ejecutar las pruebas secuencialmente y no cargar otros modelos a la vez. La coordinación del resto de IA se incorpora en la fase de integración.

## Preprocesamiento y salida

- Firma PNG/JPEG, máximo 10 MiB; 8 bits, escala de grises o RGB; no animación, DICOM, paletas o 16 bits de escala desconocida.
- Validación de dimensiones antes de cargar el array: mínimo 32 px por lado, máximo 8192 por lado y 16 megapíxeles.
- Normalización oficial XRV de `[0,255]` a aproximadamente `[-1024,1024]`; promedio de canales si RGB; `XRayCenterCrop`; `XRayResizer(224)`; float32, forma `[1,1,224,224]`.
- Original conservado; transformación solo en memoria, con hash y dimensiones de origen en la respuesta.
- Modelo CPU, `eval()` e `inference_mode()`, cuatro hilos, batch 1. Selección por nombre de Consolidation, Effusion y Cardiomegaly; validación de las 18 etiquetas y de la salida finita.

La inferencia crea la arquitectura con **`weights=None`** y carga solo safetensors local verificado. Nunca importa el script de descarga, resuelve una URL ni utiliza la caché de checkpoints de XRV. Si falta el manifest/peso o no coincide su hash, devuelve error claro. El checkpoint pickle original se conserva para procedencia pero **no se necesita ni se monta** para la prueba offline.

La respuesta JSON incluye modelo, versión, hash, dispositivo, etiquetas, preprocesamiento, `findings`, advertencias y métricas. Siempre `experimental=true`, `calibrated_probability=false`; no contiene diagnóstico ni conclusión “normal”.

Las puntuaciones usan sigmoid y normalización por puntos operativos (`op_norm`) de XRV. **No son probabilidades clínicas calibradas, ni porcentajes de certeza.** No se convierte 0,5 en un umbral clínico ni una puntuación baja en ausencia de enfermedad.

## Resultados reales observados en Windows

Equipo: Ryzen 7 5700U, Windows 11 Pro, CPU, cuatro hilos. Resultados crudos conservados localmente en `backend/.radiologia-resultados/NIH-RX-00{1,2}-windows-perfil2g.json`.

**Puntuaciones experimentales normalizadas, no probabilidades:**

| Imagen | Consolidation | Effusion | Cardiomegaly |
|---|---:|---:|---:|
| NIH-RX-001 | 0,312433 | 0,394274 | 0,621515 |
| NIH-RX-002 | 0,506897 | 0,098563 | 0,011205 |

| Imagen | Inferencias 1/2/3 (s) | Carga de parámetros (s) | Arranque/análisis completo observado (s) | RSS máxima observada del hijo |
|---|---|---:|---:|---:|
| NIH-RX-001 | 0,331 / 0,125 / 0,108 | 0,279 | 26,134 | 403.935.232 bytes (~385 MiB) |
| NIH-RX-002 | 0,276 / 0,263 / 0,359 | 0,521 | 28,928 | 404.606.976 bytes (~386 MiB) |

El tiempo completo incluye creación del proceso, importaciones y preprocesamiento; no presentar solo el pase de red como latencia HTTP futura. El pico es un máximo **observado por muestreo y RSS al final**, no un máximo absoluto de todas las asignaciones o del sistema. Una ejecución anterior de la primera muestra obtuvo ~15,7 s completos: el coste de arranque varía con carga/cachés del equipo. No se hicieron pruebas de estrés.

La primera muestra tiene etiqueta NIH débil Cardiomegaly y esa fue la mayor puntuación de las tres. La segunda, etiquetada NIH “No Finding”, obtuvo Consolidation ~0,507: esto muestra por qué no debe traducirse automáticamente un score a diagnóstico ni afirmarse precisión clínica sobre dos ejemplos. No se resuelve esa discrepancia inventando un informe.

## Prueba offline reproducible

La construcción instala dependencias **durante preparación con Internet**; la ejecución posterior se hará con `--network none`, sin alterar la red del equipo y sin levantar un servicio nuevo. Construir desde `backend/`:

```powershell
docker build -f Dockerfile.radiologia-offline-test -t sarcosistema-vision-offline:fase2 .
```

Ejecutar luego, desde `backend/`, con los artefactos preparados y sin descargas. Se montan **solo** el manifest y safetensors (no el checkpoint original ni la caché de XRV), y las muestras en lectura:

```powershell
$base = (Get-Location).Path
docker run --rm --network none --memory 2g --memory-swap 2g --cpus 4 --pids-limit 128 `
  --read-only --tmpfs /tmp:rw,size=256m,mode=1777 `
  --mount "type=bind,source=$base\.models\radiologia\manifest.json,target=/models/manifest.json,readonly" `
  --mount "type=bind,source=$base\.models\radiologia\densenet121-res224-all.safetensors,target=/models/densenet121-res224-all.safetensors,readonly" `
  --mount "type=bind,source=$base\.datasets\radiologia,target=/samples,readonly" `
  -e RUN_XRAY_OFFLINE_TESTS=1 sarcosistema-vision-offline:fase2 `
  python -m pytest -p no:cacheprovider -q -s `
  app/imagenes/tests/test_vision_offline_real.py `
  app/imagenes/tests/test_servicio_vision.py::test_timeout_mata_hijo_que_ignora_sigterm `
  app/imagenes/tests/test_vision.py::test_rechaza_rgb_png_16_bits_antes_de_importar_torch `
  --basetemp /tmp/pytest-vision --tb=short
```

**Resultado real final: 5 passed en 31,01 s.** Verificados por `docker inspect`: `network=none`, memoria 2.147.483.648 bytes, cuatro CPU, raíz de solo lectura, exit 0 y `oom_killed=false`. El proceso de prueba comprobó mediante un intento de conexión real del SO que no podía acceder a `1.1.1.1:443`; no se usó un mock de sockets. La red del host siguió intacta. Esto prueba el runtime aislado Linux en Docker sobre el equipo Windows, no que se hayan deshabilitado físicamente los adaptadores de Windows.

Las cinco pruebas cubren: ausencia de red externa; inferencia real de las dos muestras; pesos ausentes sin descarga; timeout con un hijo que ignora SIGTERM; rechazo de fuente RGB PNG de 16 bits antes de cargar Torch. La terminación escala a cierre forzado y espera a que el hijo finalice antes de liberar el lock. El control PNG inspecciona la profundidad IHDR original: comprobar solo el modo `RGB` de Pillow no era suficiente.

En el ensayo aislado, los pases de inferencia tardaron 0,265 s y 0,152 s, con RSS máxima observada de 413.540.352 y 416.899.072 bytes; los tiempos completos fueron 16,014 s y 5,922 s. Las puntuaciones tuvieron una diferencia absoluta máxima respecto de Windows de **1,1921×10⁻⁷**, compatible con pequeñas diferencias de cómputo FP32, no una medida de exactitud clínica.

El log con las salidas experimentales está en `backend/.radiologia-resultados/offline-verificacion-final.log` y su JSON extraído en `resultados-offline-final.json` (fuera de Git). Los archivos escritos en `/tmp` son volátiles y desaparecen al detener el contenedor; no intentar recuperarlos con `docker cp` tras desmontarse el tmpfs. Con `-s` las salidas de estas muestras de investigación se conservan en stdout si se desea capturarlas.

## Pruebas automatizadas

```powershell
# backend
.\.venv\Scripts\python.exe -m pytest app/imagenes/tests -q
$env:RUN_XRAY_REAL_TESTS='1'
.\.venv\Scripts\python.exe -m pytest app/imagenes/tests/test_servicio_vision.py -q
Remove-Item Env:RUN_XRAY_REAL_TESTS
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Las pruebas de preprocesamiento se omiten si no están instaladas sus dependencias opcionales; las pruebas reales nunca descargan modelos. La prueba real también exige memoria disponible, pesos y muestras preparados. Un rechazo por memoria no es una predicción falsa ni autoriza a eliminar el guard.

Verificación optativa real en Windows: **7 passed, 1 skipped en 30,09 s** en `test_servicio_vision.py`; la omisión es la prueba POSIX de SIGTERM (ejecutada y aprobada dentro de Docker). Antes hubo rechazos de la prueba real cuando la RAM cayó por debajo del mínimo: se conservaron esos resultados, no se eliminó el guard ni se inventó una predicción.

El tamaño de imagen comunicado por Docker tras la preparación fue 414.491.697 bytes; no es el consumo total de disco de wheels, venv, cachés y almacenamiento de Docker/WSL. La preparación online es más costosa que inferir una imagen y no forma parte de una solicitud clínica. No se descargaron datasets completos, CUDA ni modelos de texto.

No se ha añadido RAG, embeddings, LLM, pantalla radiológica ni una operación clínica nueva en la API. La Fase 2 termina tras las verificaciones indicadas; la integración clínica queda para fases posteriores.

### Cierre de verificación (03/11/2026)

- Suite general backend: **218 passed, 7 skipped en 26,76 s**. Las omisiones incluyen las evaluaciones optativas de IA/visión, el entorno offline y el caso POSIX; las pruebas visuales reales Windows y offline se ejecutaron por separado, con los resultados anteriores.
- Frontend: **22 passed**, lint y build correctos. No se modificaron componentes de frontend para esta fase.
- `pip check`: sin dependencias rotas. Importación fresca de `app.main`: correcta y **Torch no está cargado** al iniciar el backend manual.
- Revisión independiente: sin hallazgos críticos; los dos hallazgos importantes (RGB de 16 bits y trabajador POSIX resistente a SIGTERM) se reprodujeron antes del cambio y sus pruebas pasaron después. La guía offline pendiente se completó con el comando y evidencia real.
- Pesos preparados/conservados y ambas muestras reales procesadas en CPU. Sin entrenamiento, cambios de BD, generación de diagnósticos, RAG, LLM ni avance a otra fase. Sin commit ni push.
