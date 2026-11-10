# Fase 5 — evaluación experimental reproducible

## Estado y alcance

**Evaluación experimental completada, incluida prueba API offline. No es validación clínica ni autorización de uso asistencial.**
Se evalúa el sistema existente, sin entrenamiento, ajuste de umbrales o corrección del extractor después de observar el test. Los fallos conocidos se incluyen en los resultados.

## Entradas congeladas

### Texto sintético

[`evaluacion/casos-sinteticos.jsonl`](evaluacion/casos-sinteticos.jsonl): 300 casos, 75 positivos, 75 negativos, 75 ambiguos y 75 contradictorios; 25 por hallazgo y grupo. Cada registro dice `synthetic=true` y «CASO SINTÉTICO — NO VALIDACIÓN CLÍNICA». Contexto adulto ficticio, sin imagen auténtica emparejada. Las etiquetas se declaran en el generador, **no** se obtienen del extractor evaluado.

Se usan 100 familias lingüísticas, compartidas entre tres términos. No son 300 observaciones independientes ni una muestra representativa del lenguaje hospitalario. Referencias de autoría no experta; sin revisión médica externa. `ambiguo` como grupo incluye estados esperados `incierto` y `ambiguo`; `no_mencionado` se usa para hallazgos no descritos, nunca como ausencia de enfermedad.

### Radiografías reales NIH derivadas

60 imágenes, pacientes distintos, selección determinista por estratos antes de inferir: consolidación, derrame, cardiomegalia y «No Finding», hasta 15 por estrato. Otros hallazgos pueden coexistir. Solo PA/AP. Se contrastan IDs y etiquetas contra `Data_Entry_2017_v2020.csv.gz` de la instalación XRV. Las imágenes quedan fuera de Git, con hashes y manifiesto local.

- Proveedor: **NIH Clinical Center**; origen: https://nihcc.app.box.com/v/ChestXray-NIHCC
- Distribuidor derivado: **Chehab Lab**, https://huggingface.co/datasets/chehablab/NIHChestXR
- Revisión solicitada: `adcb330b5861dc4b1de5697e49e45ebf45d7e28c`; se conserva también la revisión observada en URL del asset y hash local. La API de filas no se asume una garantía de pinning: el manifiesto de archivos realmente recibidos es la identidad de ejecución.
- Permiso/atribución NIH: https://cloud.google.com/healthcare-api/docs/resources/public-datasets/nih-chest#license_and_attribution
- Cita: Wang X, Peng Y, Lu L, Lu Z, Bagheri M, Summers R. *ChestX-ray8: Hospital-scale Chest X-ray Database and Benchmarks on Weakly-Supervised Classification and Localization of Common Thorax Diseases*. CVPR, 2017.

Son **imágenes derivadas reducidas, no originales NIH de resolución completa**. El README del mirror menciona 244×244; se debe reportar el tamaño realmente observado en manifiesto, no asumir esa cifra. No se usa la afirmación de precisión del etiquetador publicada por el mirror como validación de estas etiquetas.

Las etiquetas NIH proceden de NLP y son débiles. Para el benchmark se aplica la convención «etiqueta ausente del conjunto NLP = negativo débil», **no** ausencia clínica demostrada. Metadatos ausentes se excluyen como desconocidos. «No Finding» no es garantía de normalidad. TorchXRayVision `all` incluyó NIH durante entrenamiento: **no se demuestra independencia de pacientes ni ausencia de fuga de entrenamiento**. La selección enriquecida, de primeras filas accesibles y no aleatoria poblacional, sesga resultados y no permite estimar prevalencia, utilidad clínica ni generalización.

VinDr-CXR ofrecía mejores referencias de radiólogos, pero exige acreditación, formación y DUA: https://physionet.org/content/vindr-cxr/1.0.0/. No se aceptó un acuerdo en nombre del usuario ni se eludió el acceso. Box no entregó archivos con el transporte textual y Google usa Requester Pays; no se incurrió en gastos. NIH derivado se eligió como alternativa **exploratoria**, no equivalente a VinDr.

### Preguntas/documentos

[`evaluacion/preguntas-rag.json`](evaluacion/preguntas-rag.json): 40 preguntas congeladas: 24 respondibles (8 por hallazgo), 8 fuera del corpus, 8 ambiguas sobre pacientes sin datos para responder. Referencias documento/sección y anclas de texto comprobadas antes de recuperar. Fuente: dos documentos ya autorizados, `PMC6958895` y `PMC4753987`, sin nuevo corpus ni LLM. Preguntas de autoría sintética no experta, con dependencia entre preguntas de una misma sección. Relevancia a nivel sección no prueba que cada fragmento responda exactamente la pregunta.

## Métricas y resultados textuales actuales

| Grupo | Correctos objetivo | Exactitud |
|---|---:|---:|
| Positivos | 74/75 | 98,67 % |
| Negativos | 63/75 | 84,00 % |
| Ambiguos | 45/75 | 60,00 % |
| Contradictorios | 60/75 | 80,00 % |
| Total | **242/300** | **80,67 %** |

Macro-F1 objetivo: **0,797869**. Las 900 etiquetas (tres por caso) se reportan aparte porque incluyen muchos `no_mencionado`; no sustituir la métrica objetivo por una cifra inflada por esos negativos textuales. Las matrices y errores por ID están en `backend/.radiologia-resultados/fase5/texto.json`.

Errores conocidos retenidos: `Consolidación?` se interpreta como descrito; `Derrame pleural no evidente.` se interpreta como descrito; una negación de derrame afecta a cardiomegalia en la misma cláusula. Las referencias de desafío exigen preservar incertidumbre y conflictos, no resolverlos automáticamente.

## Comparación con/sin RAG: qué mide

La visión y la fusión se ejecutan antes del RAG en `AnalizarEstudio`. El RAG actual recibe **la misma pregunta genérica en todos los estudios**, no el informe de cada paciente. No puede mejorar por diseño los scores visuales ni corregir el extractor. El resultado sin RAG no aporta citas; con RAG añade únicamente evidencia documental extractiva.

La ablación de 300 textos usa el caso de uso real con **scores controlados sintéticos 0,8** y replay explícito de una recuperación real a esa pregunta fija. Mide invariancia, citas y ausencia de confirmación automática, no 300 inferencias/recuperaciones independientes. La latencia de este replay no se presenta como latencia clínica ni como ahorro real de RAG. El flujo API con visión/embeddings/pgvector reales se mide por separado sobre imagen NIH y un informe demo que dice expresamente que es simulación y no su informe auténtico.

## Protocolo visual y documental

Visual: TP/FP/TN/FN, sensibilidad, especificidad, precisión, F1 al umbral técnico preexistente 0,5; AUROC por comparación de pares con empates a 0,5 y AP agrupando scores empatados. AUROC queda `null` si falta una clase; AP `null` si no hay positivos. Sin umbrales optimizados ni probabilidades calibradas. Denominadores de intentos, éxitos y errores por separado; fallos no se imputan como scores.

RAG: Recall@4 y MRR@10 contra documento+sección, solo sobre las 24 respondibles. Verificación de citas por hash de documento, rango y coincidencia exacta de texto. Precisión/recall de abstención según el protocolo de 16 preguntas no respondibles. **Una cita íntegra puede ser irrelevante**; la integridad no mide corrección clínica. En las preguntas ambiguas, devolver contexto genérico no equivale a contestar al paciente; se reporta separado del resultado de abstención estricto. No se evalúa fidelidad generativa de un LLM porque el sistema es extractivo.

### Resultados visuales reales offline

**60 seleccionadas, 60 descargadas, 60 inferencias completas, 0 pérdidas de descarga, 0 errores de inferencia.** Todas las imágenes recibidas tienen **224×224 px**. Referencias NLP débiles y posible exposición durante entrenamiento: cifras exploratorias, no sensibilidad/especificidad clínica validada. Los estratos de selección no son etiquetas mutuamente excluyentes.

| Hallazgo | Pos./neg. NLP | TP/FP/TN/FN | AUROC | AP | Sensibilidad débil | Especificidad débil | Precisión | F1 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Consolidación | 15/45 | 11/13/32/4 | 0,7970 | 0,5716 | 0,7333 | 0,7111 | 0,4583 | 0,5641 |
| Derrame pleural | 23/37 | 18/9/28/5 | 0,7861 | 0,7052 | 0,7826 | 0,7568 | 0,6667 | 0,7200 |
| Cardiomegalia | 19/41 | 16/9/32/3 | 0,9037 | 0,8647 | 0,8421 | 0,7805 | 0,6400 | 0,7273 |

No se añadieron modelos ni se cambió el umbral técnico 0,5. Consolidación presenta 13 falsos positivos respecto a la referencia débil: no puede interpretarse como prueba de enfermedad ni resolverse inventando un informe.

### Resultados documentales reales offline

Modelo: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`. Embeddings y PostgreSQL/pgvector reales sobre los dos documentos/215 fragmentos preparados. Preguntas en español y fuentes en inglés; corpus muy pequeño y no representativo.

| Medida | Resultado | Denominador/interpretación |
|---|---:|---|
| Recall@4 documento+sección | 0,9167 | 22/24 secciones pertinentes entre primeras cuatro recuperaciones |
| MRR@10 | 0,6019 | 24 preguntas respondibles |
| Respondibles con alguna cita emitida | 58,33 % | 14/24; **no exactitud de respuesta** |
| Citas estructuralmente íntegras | 100 % | 41/41 citas; no garantiza relevancia |
| Precisión de abstención | 52,38 % | 11 abstenciones pertinentes /21 abstenciones |
| Recall de abstención | 68,75 % | 11/16 no respondibles según protocolo |
| Fuera de corpus sin evidencia | 8/8 | Consultas fuera de los temas/documentos |
| Ambiguas de paciente sin evidencia | 3/8 | En las otras 5 devuelve contexto genérico, no una respuesta del paciente |
| Respondibles con abstención | 10/24 | Limitación del filtrado/distancia/alcance temático actual |

| Hallazgo de pregunta | Recall@4 | MRR@10 | Preguntas con citas |
|---|---:|---:|---:|
| Consolidación | 1,0000 | 0,6354 | 4/8 |
| Derrame pleural | 0,7500 | 0,4722 | 3/8 |
| Cardiomegalia | 1,0000 | 0,6979 | 7/8 |

La discrepancia entre recall de sección y citas emitidas muestra que recuperar una sección pertinente no basta para generar una respuesta útil. No se midió exactitud clínica, completitud de respuesta ni revisión experta de pertinencia por cita. La falta de un documento dedicado a cardiomegalia y la pregunta fija de integración limitan la interpretación aun cuando haya recuperación.

### Resultado de ablación contractual

300 pares con/sin RAG: scores idénticos **300/300**, fusión textual idéntica **300/300**, diagnósticos confirmados automáticamente **0**. Sin RAG: cero citas por caso. Con RAG: cuatro citas por caso, reutilizadas desde **una sola consulta fija** real. Por tanto, añadir RAG aporta trazabilidad documental pero **esta prueba no demuestra mejora diagnóstica, adaptación al caso ni beneficio clínico**. La ejecución real API se documenta aparte; no se cuentan estas 600 llamadas contractuales como inferencias visuales reales.

## Reproducción

Desde `backend/`, Python 3.12 y artefactos opcionales existentes:

```powershell
.\.venv\Scripts\python.exe -m scripts.preparar_evaluacion_radiologia --descargar
.\.venv\Scripts\python.exe -m scripts.evaluar_radiologia --visual --rag
.\.venv\Scripts\python.exe -m pytest -q
```

La preparación rechaza sobrescribir el manifiesto. Los resultados usan archivos propios de evaluación; para conservar varias ejecuciones pasar `--salida` distinto. No ejecutar el preparador demo sobre la base habitual. Los comandos RAG solo leen el corpus indexado; una base nueva necesita indexación explícita.

## Offline y hardware

Lote real: `sarco-fase5-evaluacion-a3536ff7` con PostgreSQL `sarco-fase5-db-a3536ff7`. Base nueva creada desde bootstrap y migrada a0012, con cuenta/estudio reservados ficticios e indexación local. PostgreSQL usa `--network none`; runner `--network container:<postgres>`. Ambos sin puertos publicados. Solo comparten loopback aislado; el intento de conexión del SO a `1.1.1.1:443` falla. No se desconecta físicamente Windows ni se afirma ejecución del navegador dentro de esa frontera.

El lote completo terminó **exit0**, **417,790s**, con 300 textos, 60 imágenes y 40 preguntas. Runtime Python3.12.16/Linux WSL2; el host usa Python3.12. El contenedor de evaluación inicial utiliza imagen previa a las dos mejoras de robustez del evaluador (denominadores/checkpoints); se conservan sus resultados y se repite RAG con la revisión actualizada. No hubo fallos de descarga/inferencia en ese lote, por lo que esos cambios no alteran sus métricas.

Repetición documental actualizada: `sarco-fase5-revision-a3536ff7`, **40/40 completadas, 0 errores**, mismos Recall/MRR/abstención/citas que el primer lote, **exit0**. Orquestador26,174s; tiempo externo Docker29,875s; embeddings del lote23,364s. Los fallos ahora se conservan por pregunta y los denominadores visuales incluyen también pérdidas de preparación; pruebas de regresión específicas RED→GREEN.

API real: `sarco-fase5-api-a3536ff7`, **exit0**,42,006s observados desde el host incluyendo arranque Docker y comprobaciones. Verificados JWT/rol, lectura de imagen local, encolado/análisis con visión/embeddings/pgvector reales, cuatro citas, reenvío idempotente, revisión ficticia persistida, conflicto de versión HTTP409 e informe publicado sin cambios. La inferencia visual de ese flujo tardó7,212s completos. No se midió una segunda API real sin RAG: la comparación sin RAG es la ablación contractual descrita, no una comparación de latencia clínica.

`docker inspect` filtrado confirmó `OOMKilled=false`, exit0 en los tres runners, rootfs de solo lectura, límites de recursos y ausencia de puertos. PostgreSQL sigue siendo una base efímera aislada, no la base de la instalación habitual. Resumen agregado versionable y hashes de salidas: [`evaluacion/resumen-resultados.json`](evaluacion/resumen-resultados.json). JSON crudos y logs permanecen en `backend/.radiologia-resultados/fase5/offline/`; `revision/` conserva la repetición corregida. La evidencia no incluye tokens, claves, datos clínicos reales ni un navegador offline.

Hardware observado: **Ryzen7 5700U, 8 núcleos/16 hilos, 16GB RAM física**, Windows11/WSL2. La VM Linux expuso 7,97GB de RAM y 6,22GB disponibles al inicio. Runner limitado a **4 CPU, 3GiB de RAM/swap total**, raíz solo lectura, tmpfs512MiB; PostgreSQL limitado a768MiB. Sin GPU ni modelos concurrentes.

| Recursos/tiempo | Observación |
|---|---:|
| Latencia visual completa (n=60), mediana | 4,532s |
| Latencia visual completa p95, nearest-rank | 11,614s |
| Latencia completa mínima/máxima | 3,442/25,349s |
| Solo pase de red visual, mediana | 0,111s; **no latencia API** |
| RSS máxima observada de trabajador visual | 421.994.496 bytes (~402,45MiB), muestreada, no máximo absoluto |
| Embeddings lote 41 consultas | 24,153s, incluye pregunta fija extra; no 40 arranques individuales |
| Recuperación/respuesta por pregunta, mediana | 0,02475s, **excluye embeddings** |
| Imagen Docker de evaluación inicial | 493.621.990 bytes; no disco total Docker/WSL |
| Carpeta modelos visuales preparada | 56.666.997 bytes; incluye checkpoint original **no montado** |
| Carpeta embeddings preparada | 499.566.768 bytes |
| Dos documentos fuente | 298.140 bytes |
| Imágenes derivadas descargadas | 336.719 bytes; caché de metadatos/manifiestos adicional |

Requisitos del piloto: conservar guardas visuales generales de4GiB libres; el perfil explícito de2GiB se usó solo para estas imágenes pequeñas y fixtures512px, no es un mínimo validado para imágenes arbitrarias. Embeddings exige2GiB libres. Recomendación operativa de laboratorio: equipo16GB, al menos4GiB libres antes de arrancar, 4hilos CPU y varios GB adicionales de disco para dependencias/Docker/WSL. Es recomendación prudente, no capacidad certificada ni prueba de carga. No se ha medido el pico RSS de embeddings ni el consumo máximo conjunto del sistema; el límite Docker no es consumo observado.

### Comandos de reproducción offline (PowerShell, desde backend)

Preparar antes las imágenes Docker de Fases2/3/4 según sus guías y construir:

```powershell
docker build -f Dockerfile.imagenes-evaluacion-test -t sarcosistema-evaluacion:fase5 .
$base = (Get-Location).Path
$id = [guid]::NewGuid().ToString('N').Substring(0,8)
$db = "fase5_$id"
$contenedor = "sarco-fase5-db-$id"
$privado = Join-Path $env:LOCALAPPDATA "Temp\opencode\fase5_$id"
New-Item -ItemType Directory -Path $privado | Out-Null
$clave = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$jwt = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$envfile = Join-Path $privado 'runtime.env'
@("POSTGRES_USER=hospital", "POSTGRES_PASSWORD=$clave", "POSTGRES_DB=$db",
  "DATABASE_URL=postgresql+asyncpg://hospital:${clave}@127.0.0.1:5432/$db",
  "JWT_SECRET_KEY=$jwt", 'RADIOLOGY_AI_ENABLED=true', 'RADIOLOGY_STORAGE_DIR=/samples',
  'RADIOLOGY_VISION_MIN_FREE_MIB=2048', 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
  'PYTHONDONTWRITEBYTECODE=1') | Set-Content -Encoding ascii $envfile
docker run -d --name $contenedor --network none --env-file $envfile --memory 768m --tmpfs /var/lib/postgresql/data:rw,size=512m pgvector/pgvector:pg16
docker exec $contenedor pg_isready -U hospital -d $db
# No continuar hasta que pg_isready acepte conexiones. Esta base es NUEVA.
docker cp ..\database\schema.sql "${contenedor}:/tmp/bootstrap.sql"
docker exec $contenedor psql -q -v ON_ERROR_STOP=1 -U hospital -d $db -f /tmp/bootstrap.sql
$salida = Join-Path $privado 'resultados'
New-Item -ItemType Directory -Path $salida | Out-Null
$comun = @('run', '--network', "container:$contenedor", '--env-file', $envfile,
 '--memory', '3g', '--memory-swap', '3g', '--cpus', '4', '--pids-limit', '256',
 '--read-only', '--tmpfs', '/tmp:rw,size=512m,mode=1777',
 '--mount', "type=bind,source=$base\.models\radiologia\manifest.json,target=/app/.models/radiologia/manifest.json,readonly",
 '--mount', "type=bind,source=$base\.models\radiologia\densenet121-res224-all.safetensors,target=/app/.models/radiologia/densenet121-res224-all.safetensors,readonly",
 '--mount', "type=bind,source=$base\.models\rag-torax,target=/app/.models/rag-torax,readonly",
 '--mount', "type=bind,source=$base\.datasets\rag-torax,target=/app/.datasets/rag-torax,readonly",
 '--mount', "type=bind,source=$base\.datasets\evaluacion-fase5,target=/app/.datasets/evaluacion-fase5,readonly",
 '--mount', "type=bind,source=$base\.datasets\radiologia,target=/samples,readonly",
 '--mount', "type=bind,source=$base\..\docs\imagenes\evaluacion,target=/entradas,readonly",
 '--mount', "type=bind,source=$salida,target=/resultados")
docker @comun --rm sarcosistema-evaluacion:fase5 python -m alembic upgrade head
docker @comun --rm sarcosistema-evaluacion:fase5 python -m scripts.evaluacion_radiologia.preparar_demo_offline
docker @comun --rm sarcosistema-evaluacion:fase5 python -m scripts.consultar_rag_torax --indexar
docker @comun --name "sarco-fase5-evaluacion-$id" sarcosistema-evaluacion:fase5
docker @comun --name "sarco-fase5-api-$id" sarcosistema-evaluacion:fase5 python -m scripts.verificar_imagenes_offline
```

Revisar el código de salida **en cada paso**, no continuar tras errores. No paralelizar inferencias ni indexación. Los contenedores finales se conservan para `docker inspect`/`docker logs`; los JSON persisten en `$salida`. No imprimir/versionar `$envfile` ni usar sus claves fuera de esta base efímera. No usar `docker inspect` sin filtro en informes porque expone el entorno. La imagen base de evaluación es una dependencia de preparación, no una descarga durante runtime. Destruir/retirar recursos solo por nombre y tras conservar la evidencia; no ejecutar limpieza global Docker ni tocar el volumen original.

## Verificación y revisión

- Suite final predeterminada: **298 passed, 11 skipped in20,77s**. RAG PostgreSQL optativo ejecutado en proceso separado: **3 passed in0,19s**. Importación de `app.main` y `pip check` correctos. Frontend no modificado en Fase5; no se repitieron sus comandos ni se declara nueva evidencia de navegador.
- Omisiones predeterminadas: `test_archivos_imagenes.py` (1, symlink requiere privilegios Windows); `test_rag_offline_real.py` (2, flags del harness anterior); `test_rag_repository.py` (1, flag optativo, ejecutado luego); `test_servicio_vision.py` (2, caso POSIX y flag de inferencia); `test_vision_offline_real.py` (3, flags del contenedor anterior); `test_extraccion_modelo_local.py` (2, Ollama/extracción de Consultas fuera de esta evaluación). El lote/API de Fase5 sí ejecutaron modelos reales offline, pero no se afirma haber repetido todos los escenarios negativos de esos harness anteriores.
- Revisión independiente: dos riesgos del evaluador corregidos (pérdidas de descarga fuera del denominador y pérdida de resultados RAG parciales), cada uno con prueba que falló antes del cambio y pasó después. Sin cambios a producción ni al modelo. Limitaciones de relevancia a nivel sección, referencias sintéticas no expertas y replay conservadas explícitamente, no disfrazadas de precisión clínica.
- Sin commits, push, entrenamiento, nuevo LLM ni cambios de esquema/credenciales. Código, corpus sintético y resúmenes nuevos quedan en el árbol de trabajo junto con el trabajo previo conservado.
- Comprobación adicional: las AUROC y AP de las tres clases sobre los60 resultados coinciden con `sklearn.metrics.roc_auc_score` y `average_precision_score` (tolerancia1e-12); los300 registros congelados coinciden exactamente con el generador reproducible.

## Conclusiones

El extractor no es robusto ante ambigüedad y negación: el resultado sintético ya impide presentar el sistema como validado. Entrenar un modelo nuevo no está justificado por estos textos ni por un benchmark NIH pequeño, débil y potencialmente visto durante entrenamiento. Antes de valorar entrenamiento hacen falta referencias independientes de expertos, evaluación externa y una pregunta clínica/objetivo de uso definidos. No se ha entrenado ni ajustado ningún modelo.

La visión CPU y la recuperación local funcionan sin Internet en la frontera comprobada. El benchmark visual muestra discriminación exploratoria y falsos positivos/negativos frente a referencias débiles; no permite certificar generalización. El RAG recupera secciones pertinentes con frecuencia, pero emite citas en solo14/24 preguntas respondibles y añade contexto genérico en5/8 consultas ambiguas sobre pacientes. Citas íntegras y revisión humana explícita mejoran trazabilidad, **no prueban corrección diagnóstica**. Prioridad posterior: corregir/revalidar negaciones e incertidumbre en un conjunto de desarrollo separado y conseguir evaluación independiente con revisión experta; no optimizar sobre estos300 casos y presentar luego el mismo conjunto como test nuevo.
