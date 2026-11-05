# RAG local de tórax — Fase 3

Prototipo académico, no diagnóstico. Sin frontend ni LLM. Las consultas devuelven citas documentales literales en su idioma original y no extraen hallazgos confirmados de un paciente. El campo `informe_original` conserva la consulta; no representa un informe clínico interpretado. La fusión de imagen e informe pertenece a la siguiente integración solicitada.

## Preparación con Internet

Desde `backend/`, con Python 3.12 y PyTorch CPU previamente preparado:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-rag.txt
.\.venv\Scripts\python.exe -m scripts.preparar_rag_torax --descargar
.\.venv\Scripts\python.exe -m alembic upgrade head
```

No reejecutar el bootstrap de SQL ni eliminar volúmenes. La migración `20261103_0008` habilita la extensión vector y agrega únicamente `rag_torax_documento` y `rag_torax_fragmento`. El downgrade se bloquea para no borrar documentación ni una extensión compartida automáticamente.

El modelo es `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, Apache-2.0; 384 dimensiones, mean pooling, normalización L2 y máximo 128 tokens. Safetensors ocupa 448,84 MiB; SHA-256 `eaa086f0ffee582aeb45b36e34cdd1fe2d6de2bef61f8a559a1bbc9bd955917b`. Los prefijos E5 no se aplican a este modelo. Artefactos en `.models/rag-torax`, documentos en `.datasets/rag-torax`, excluidos de Git.

## Corpus verificable

Dos artículos completos en XML JATS descargados mediante Europe PMC. No se usaron casos sintéticos como evidencia médica:

- **Chest radiography in adult critical care unit: A pictorial review**, https://pmc.ncbi.nlm.nih.gov/articles/PMC6958895/ . CC BY-NC-SA 4.0: atribución, uso no comercial y compartir derivados bajo la misma licencia. Consultar autores y referencia bibliográfica en el XML original y el artículo enlazado.
- **Pleural effusion: diagnosis, treatment, and management**, https://pmc.ncbi.nlm.nih.gov/articles/PMC4753987/ . El permiso explícito permite uso no comercial con cita del trabajo original. No se atribuye una licencia CC más amplia que la declarada por la fuente.

Los manifiestos conservan URL, hash, licencia, título y versión del extractor. La extracción omite bibliografía y figuras y conserva 215 fragmentos de párrafos. Las referencias incluyen artículo, sección, SHA-256 del XML y offsets de caracteres del texto extraído; **no se inventan números de página**. Los fragmentos se comprueban literalmente contra ese texto. El corpus es pequeño y no representa una guía clínica actualizada o validada institucionalmente.

## Uso local

```powershell
.\.venv\Scripts\python.exe -m scripts.consultar_rag_torax --indexar
.\.venv\Scripts\python.exe -m scripts.consultar_rag_torax --pregunta "¿Qué signos radiográficos puede tener el derrame pleural?"
```

En runtime se verifica integridad y se usa `local_files_only=True`, `trust_remote_code=False`, safetensors y variables offline. No se importan scripts de descarga. Ausencia de preparación da error, no inicia descarga. Ingesta parametrizada, idempotente por documento/fragmento/modelo; cambios de contenido requieren nueva versión. Búsqueda coseno exacta en pgvector, sin aproximación ANN para este corpus reducido.

El mínimo general para embeddings es 2 GiB libres. Cada lote vive en un trabajador CPU efímero con dos hilos y timeout de 180 s; terminate/kill y recolección del hijo liberan también bibliotecas/allocators. El lock de archivo se comparte con visión cuando ambos usan el mismo directorio temporal. No se cargan simultáneamente ambos modelos en el flujo previsto.

Salida `evidencia_recuperada` significa relación documental, no que la consulta clínica esté resuelta. `informacion_insuficiente` se devuelve si faltan fragmentos sustentables. Umbral de distancia 0,45 y filtros temáticos son heurísticas del prototipo, no calibración de relevancia. La similitud por sí sola no basta: sensibilidad de biopsia/CT no puede usarse para responder limitaciones de RX. No se ofrecen tratamientos automáticos ni conclusiones sobre la imagen.

## Prueba real sin salida a Internet

La imagen se construye online con `Dockerfile.rag-offline-test`, reutilizando la imagen de verificación CPU de Fase 2. El runtime usa una red Docker **interna** para acceder a PostgreSQL local de prueba; no sirve `--network none` para una prueba de dos contenedores. No se cambia firewall ni adaptadores del host. La base de prueba es temporal y distinta del volumen de SarcoSistema.

Parámetros empleados: PostgreSQL con 384 MiB, proceso RAG con límite 3 GiB y dos CPU, raíz readonly, modelos/corpus readonly, tmpfs 128 MiB. Perfil de test interno 1536 MiB libres dentro de esa cuota, sin alterar el mínimo general 2048 MiB del servicio. La red bloquea salida externa y una conexión real a 1.1.1.1:443 debe fallar.

Primera ejecución: indexó 2 documentos/215 fragmentos pero falló en la consulta posterior por memoria retenida en el proceso. Se aisló el modelo en un hijo efímero. Segunda ejecución: 2 pruebas aprobadas en 285 s con embeddings, ingesta, búsqueda y abstención reales. Revisión manual de resultados detectó un fragmento de CT/biopsia incorrectamente relacionado con limitaciones de RX; regresión reproducida en prueba unitaria y corregida con filtro de modalidad. La repetición offline de calidad final sigue pendiente de resultado; no considerar cerrada la fase hasta registrarlo.

Las primeras consultas necesitan arranque/importaciones, hash y carga de ~449 MiB; no extrapolar una latencia de red aislada a una petición HTTP. La futura integración debe usar trabajos controlados y estado visible, no bloquear indefinidamente el servidor.

### Reproducción del entorno aislado

Desde `backend/`, con Docker disponible y RAM suficiente. Cada ejecución crea nombres propios y una base temporal; no monta el volumen de la aplicación ni publica puertos:

```powershell
docker build -f Dockerfile.rag-offline-test -t sarcosistema-rag-offline:fase3 .
$base = (Get-Location).Path
$sufijo = [guid]::NewGuid().ToString('N').Substring(0,8)
$red = "sarco-rag-red-$sufijo"
$db = "sarco-rag-db-$sufijo"
$prueba = "sarco-rag-test-$sufijo"
docker network create --internal $red
docker run -d --name $db --network $red --network-alias rag-db `
  --memory 384m --cpus 1 --tmpfs /var/lib/postgresql/data:rw,size=256m `
  -e POSTGRES_USER=rag_test -e POSTGRES_PASSWORD=rag_test_local_only `
  -e POSTGRES_DB=rag_test pgvector/pgvector:pg16
docker exec $db pg_isready -U rag_test -d rag_test
# Continuar solo cuando pg_isready indique que acepta conexiones.
docker run --name $prueba --network $red --memory 3g --memory-swap 3g `
  --cpus 2 --pids-limit 128 --read-only --tmpfs /tmp:rw,size=128m,mode=1777 `
  --mount "type=bind,source=$base\.models\rag-torax,target=/models,readonly" `
  --mount "type=bind,source=$base\.datasets\rag-torax,target=/corpus,readonly" `
  -e RUN_RAG_OFFLINE_TESTS=1 `
  -e DATABASE_URL=postgresql+asyncpg://rag_test:rag_test_local_only@rag-db:5432/rag_test `
  -e JWT_SECRET_KEY=offline_test_ficticio_no_clinico `
  sarcosistema-rag-offline:fase3 python -m pytest -p no:cacheprovider -q -s `
  app/imagenes/tests/test_rag_offline_real.py `
  app/imagenes/tests/test_rag_corpus.py::test_licencia_ambigua_o_negada_se_rechaza `
  app/imagenes/tests/test_rag_consulta.py::test_comparacion_ct_rx_no_atribuye_sensibilidad_a_rx `
  --basetemp /tmp/pytest-rag --tb=short
docker inspect $prueba --format 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} readonly={{.HostConfig.ReadonlyRootfs}}'
docker network inspect $red --format 'internal={{.Internal}}'
# Detener solo la base temporal propia; su tmpfs es volátil.
docker stop $db
```

Las credenciales de estos comandos son solo del contenedor ficticio efímero, no del hospital. En la ejecución de verificación se usaron nombres fijos identificables para conservar evidencia; los comandos anteriores evitan colisionar al repetir. No es necesario borrar ni reiniciar PostgreSQL de SarcoSistema.

### Revisión independiente y regresiones

Tres hallazgos importantes reproducidos y corregidos: atribución ambigua de sensibilidad de CT a RX en frases comparativas (abstención conservadora), imposibilidad de reanudar preparación tras completar corpus y fallar modelo (etapas ahora independientes), y aceptación de licencia genérica o negada (ahora permiso explícito reconocido). Las pruebas específicas fallaron antes de los cambios y pasaron después. Suite general posterior: 248 passed, 10 skipped; build frontend correcto.

Observaciones menores pendientes: cobertura unitaria específica de todos los caminos de timeout/EOF/escalamiento del trabajador de embeddings; filtro bilingüe uniforme de preguntas de tratamiento. El generador actual solo muestra citas sin emitir recomendaciones, pero no interpretar su filtro de palabras como una barrera exhaustiva de seguridad o como clasificación clínica. La futura integración debe conservar revisión humana y no promover texto recuperado a recomendación.

### Resultado offline final

Después de las correcciones de revisión: **5 passed en 344,22 s**. Incluye corpus real de 2 artículos/215 fragmentos, embeddings MiniLM locales, búsqueda PostgreSQL/pgvector, referencias literales, abstención por evidencia insuficiente y consulta ajena, rechazo de licencias ambiguas/negadas y comparación CT/RX ambigua. Una consulta de limitaciones de RX devuelve información insuficiente: no se sustituye por la sensibilidad de una biopsia.

Inspección real: red `internal=true`, salida del proceso 0, `oom=false`, raíz readonly, cuota 3.221.225.472 bytes. El intento de conexión externa del sistema operativo falló según lo esperado. No se alteró la conectividad de Windows. La base temporal propia se detuvo tras verificar; no se borraron contenedores ni volúmenes existentes. Los 344,22 s corresponden al conjunto de prueba con indexación y varias consultas, no a la latencia de una sola consulta.
