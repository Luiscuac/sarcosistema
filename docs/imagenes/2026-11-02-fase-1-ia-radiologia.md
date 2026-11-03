# IA radiológica local — Fase 1: análisis y propuesta técnica

Fecha: 02/11/2026. **Solo análisis**: no se instalaron dependencias, descargaron pesos/datasets, crearon migraciones ni modificó la interfaz. No se apagó la red ni se hizo inferencia radiológica. Las consultas de inspección de PostgreSQL se ejecutaron en transacción de solo lectura; las pruebas de integración existentes usan datos ficticios y rollback.

## 1. Resultado ejecutivo

El hardware permite plantear una demostración CPU por etapas, pero **hoy no se autoriza técnicamente cargar la pila propuesta con la RAM libre observada**: 2,15 GiB. Antes de la Fase 2 conviene liberar memoria mediante acciones del usuario y repetir la medición. Se propone un umbral conservador configurable de 4 GiB libres como condición inicial, no como medición del consumo del modelo ni garantía de suficiencia.

Dos premisas del encargo necesitan corregirse respecto de este checkout:

1. **Rayos X aún no tiene implementación funcional en esta rama.** `backend/app/imagenes/router.py` solo declara el prefijo `/imagenes`; no contiene endpoints. `storage.py` lanza `NotImplementedError`. No hay feature ni ruta de imágenes/radiología en React y el inicio solo habilita Laboratorio y Consulta Médica. No existe una pantalla de Rayos X que podamos simplemente extender. Se deberá acordar/construir la base mínima del módulo en la Fase 6, dentro de SarcoSistema y con el estilo existente, o traer una implementación real que esté en otra rama; no se presupone su existencia.
2. **La imagen Docker contiene pgvector, pero la BD no lo tiene habilitado.** `pg_available_extensions` ofrece `vector` 0.8.7; `pg_extension` no contiene esa extensión y no hay columnas vectoriales. No se habilitó nada durante esta fase.

Estado Git inicial: rama `main`, con modificaciones locales previas en documentación, acceso, Laboratorio, consultas, audio, Compose y pruebas. Se conservaron todas. Este informe es el único archivo nuevo de esta fase.

## 2. Arquitectura y componentes reutilizables

- Backend: Python 3.12.10, FastAPI/Pydantic v2, SQLAlchemy async + asyncpg, monolito modular en `backend/app/`. Mantener `domain/`, `application/`, `infrastructure/`, `presentation/` y paquetes namespace sin `__init__.py` innecesarios.
- Composición: `app/main.py` ya incluye el router de imágenes. IA común se compone en `app/ia/router.py`; no duplicar prefijos ni enlazar sus routers internos directamente.
- Autenticación: JWT + Argon2id; `usuario_actual` consulta la identidad y `requiere_rol` aplica autorización. Existen roles activos `imagenes` y `medico`, además de `laboratorio`. La matriz de acceso al nuevo análisis y su revisión se concretará por acción, no se asumirá acceso universal por estar autenticado.
- Transacciones/auditoría: reutilizar `get_db`, repositorios sin commit propio y `auditoria_accion`. No mantener una transacción HTTP abierta mientras se ejecuta un modelo pesado.
- React/Vite: organización por features, Axios compartido, React Query y `ProtectedRoute`. El inicio/rutas nuevos deben respetar permisos; el backend sigue decidiendo el acceso.
- Referencia visual inspeccionada: `LaboratorioPage.jsx`, sidebar/topbar, tablas, modales/formularios y `laboratorio.css`. Tokens globales: acento `#0f766e`, fondo `#f7f8fa`, bordes `#e2e5ea`, tipografía Inter local. Sidebar 224 px y topbar 72 px. Reutilizar tokens, botón compartido y patrones; no importar lógica de Laboratorio como lógica de imágenes.
- Inter se empaqueta con `@fontsource/inter`. La inspección de URLs de `frontend/src` no encontró recursos/CDNs externos indispensables; sí endpoints locales del backend y del agente Windows.
- IA actual: Whisper local para audio y extractor SOAP mediante Ollama/httpx con validación estructurada, timeout, semáforo, loopback, `trust_env=False` y sin redirects. Reutilizar esos principios y transporte, **no** el prompt SOAP como si fuera interpretación radiológica.
- No existen actualmente procesador de radiografías, embeddings, RAG ni generador radiológico. Whisper no analiza imágenes y `qwen2.5:3b` actual es un modelo de texto, no un modelo visual.

## 3. Hardware realmente medido

| Recurso | Observación |
|---|---|
| Sistema | Windows 11 Pro, 64 bits |
| CPU | AMD Ryzen 7 5700U, 8 núcleos y 16 hilos |
| RAM utilizable informada por Windows | 15,33 GiB |
| RAM libre al medir | **2,15 GiB**, menos que los 4,1 GB del encargo |
| GPU | Radeon integrada; WMI informa 512 MiB de memoria dedicada |
| Disco C: libre | 109,57 GiB |
| Ollama | Responde en `127.0.0.1:11434` |
| Modelo instalado | `qwen2.5:3b`, 1.929.912.432 bytes de artefacto según `/api/tags` |
| Modelos cargados al consultar `/api/ps` | Ninguno |

La RAM libre varía con navegador, Docker y otros programas. La memoria gráfica compartida no es una GPU CUDA de 16 GB. No se ejecutaron pruebas de estrés ni se cargó un LLM para medirlo.

Política propuesta: CPU, batch 1, empezar con 4 hilos, una sola inferencia pesada global, comprobación de RAM antes de cada etapa, timeout configurable y devolución de error recuperable si falta memoria. No cerrar procesos del usuario ni descargar recursos para intentar forzar el análisis.

## 4. BD real y almacenamiento actual

Verificado PostgreSQL **16.15** en Compose (`localhost:5432`), Alembic **20261027_0007**. Existen `paciente`, `usuario`, `trabajador`, `medico`, `solicitud`, `estudio_solicitado`, `tipo_estudio`, `servicio`, `informe_imagen`, `archivo_imagen`, `ia_generacion`, `ia_fuente` y auditoría.

- `servicio` contiene `IMG` activo; su catálogo `tipo_estudio` está **vacío** en esta base.
- `informe_imagen` vincula `estudio_id`, versión, `descripcion_texto`, estado, motivo/versión anterior y publicación. Hay **0 informes**.
- `archivo_imagen` referencia un informe y almacena nombre, `url_archivo`, MIME, bytes, SHA-256, estado y creador. Hay **0 archivos**. La tabla permite referencias, pero **no hay almacenamiento local de archivos implementado**; no afirmar que exista una radiografía accesible.
- `ia_generacion` requiere `consulta_id` y `paciente_id`; `ia_fuente` depende de esa generación. No son un corpus RAG y no almacenan embeddings. No fabricar una consulta para satisfacer el FK de un análisis de estudio.
- No hay tablas de documentos/fragmentos vectoriales operativas. El comentario `meta.embeddings` del SQL no demuestra que exista una tabla útil: se contrastó el catálogo real.

Propuesta para fases posteriores, sujeta a revisión antes de crear migraciones:

- Fase 3: habilitar `vector` mediante migración incremental y agregar documento/fragmento de conocimiento con título, procedencia, referencia/URL, licencia, fecha/revisión, hash, categoría, texto y vector **384**. Registrar modelo/revisión del embedding; no mezclar dimensiones/modelos incompatibles.
- Fase 6: almacenar análisis experimental separado, ligado a `estudio_solicitado`, archivo/hash y versión de informe. Guardar modelos/versión/hash, puntuaciones, extracción, discrepancias, fragmentos/citas usados, respuesta, actor solicitante y revisión médica. Definir si ampliar `ia_generacion` de forma compatible o usar una tabla específica; con las restricciones actuales, una tabla específica evita forzar `consulta_id`. No decidir esa modificación silenciosamente.
- Conservar originales/informes publicados; las propuestas IA no son una edición ni una publicación de ellos. Auditoría de solicitud/revisión sin textos clínicos en logs.

## 5. Dependencias: instalado vs. pendiente

Disponibles en `backend/.venv`: NumPy 2.5.3, ONNX Runtime 1.31.0, huggingface-hub 2.2.0, pgvector Python 0.3.4, SQLAlchemy 2.0.35, asyncpg 0.29.0, httpx 0.27.2, faster-whisper 1.2.1 y PyAV 16.1.0.

**No instalados:** torch, torchvision, torchxrayvision, Pillow, scikit-image, sentence-transformers, transformers, safetensors y psutil. No se importaron ni instalaron para medirlos.

Metadatos públicos consultados: TorchXRayVision **1.5.7** declara torch, torchvision, scikit-image, tqdm, NumPy, pandas, requests, Pillow e imageio. Que el paquete declare Python `>=3.6` no certifica la combinación concreta con Python 3.12/NumPy 2.5.3. Antes de instalar en Fase 2 se resolverán versiones compatibles de torch/torchvision **CPU**, NumPy y dependencias; no instalar CUDA por defecto ni actualizar indiscriminadamente el entorno de Whisper.

Mantener dependencias radiológicas opcionales en un archivo específico y documentar versiones probadas. `psutil` servirá para medir RAM del sistema/proceso; las mediciones de Torch y tiempos solo se harán cuando esté instalado. No añadir Redis, Celery, otra BD o un servidor de aplicación independiente.

## 6. Modelo visual recomendado y protocolo de Fase 2

**Candidato:** TorchXRayVision DenseNet-121 `densenet121-res224-all`, CPU. El mapa de pesos oficial incluye **Consolidation**, **Effusion** y **Cardiomegaly** entre 18 salidas entrenadas. Seleccionar etiquetas por nombre desde el modelo, no por índices supuestos. No usar pesos `rsna` para estas tres tareas: no entrenan las tres etiquetas requeridas.

El artefacto oficial consultado declara **28.382.008 bytes (~28,4 MB)**. Esto **no** incluye PyTorch, sus dependencias, activaciones o el coste de importar el runtime. No es una medición de RAM ni tiempo de inferencia. El código del repositorio tiene licencia Apache 2.0; las condiciones de pesos/datasets/documentos deben comprobarse por separado antes de redistribuirlos.

Protocolo propuesto para la siguiente fase:

1. Repetir medición de recursos; si no alcanza el umbral acordado, detenerse y pedir al usuario liberar RAM, no matar procesos.
2. Instalar solo versiones CPU compatibles en la preparación aprobada. Registrar versiones y hashes. Descargar **un** peso oficial y **una** radiografía de investigación con procedencia/licencia verificadas; no el dataset completo.
3. Primera entrada: tórax frontal AP/PA, PNG/JPEG exportado y desidentificado, 8 bits. Dejar DICOM, imágenes de 16 bits sin escala conocida, otras modalidades y laterales fuera de esta primera prueba. Un archivo PNG válido no demuestra por sí solo que sea un tórax: comprobar la selección/metadata del estudio y exigir confirmación humana, sin prometer detección automática de modalidad.
4. Validar firma/formato, tamaño comprimido y píxeles antes de decodificar por completo; limitar dimensiones y rechazar bombas de descompresión/archivos animados. Propuesta inicial ajustable: 10 MiB y 16 megapíxeles, a validar con las imágenes seleccionadas. No modificar el original ni servir rutas arbitrarias del host.
5. Seguir el flujo oficial: normalizar 8 bits con máximo 255 al rango aproximado **[-1024, 1024]**; convertir a un canal; `XRayCenterCrop`; `XRayResizer(224)`; `float32`; tensor **[1, 1, 224, 224]**. Sin aumentos aleatorios ni normalización ImageNet. Registrar preprocesamiento y hash de original/derivado.
6. `eval()` + `torch.inference_mode()`, CPU, batch 1. Conservar versión y postproceso: el código oficial puede aplicar sigmoid y `op_norm` basado en puntos operativos. **No son probabilidades clínicas calibradas ni un 0,5 universal validado**. No dar porcentajes de certeza ni concluir “normal” por puntuaciones bajas.
7. Carga de pesos solo desde artefacto local aprobado, hash verificado. El constructor oficial intenta descargar si no encuentra caché: **no basta usarlo sin controles**. Preparar una carga local sin resolución remota (y, si es necesario, convertir el checkpoint de confianza a estado tensorial durante preparación, verificando equivalencia). No cargar checkpoints subidos por usuarios ni hacer deserialización insegura de archivos desconocidos.
8. Medir arranque, inferencia en frío/caliente, RSS y RAM disponible; comprobar que SarcoSistema siga respondiendo. No hay métricas de este modelo todavía.
9. Probar de verdad sin acceso a Internet y con pesos ausentes: resultado válido en el primer caso y error claro en el segundo, nunca una descarga automática. Detenerse al cerrar la Fase 2; no añadir LLM aún.

## 7. Plan de RAG local — Fase 3

Modelo candidato solicitado: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, CPU, salida **384 dimensiones**, español soportado y licencia del modelo Apache 2.0 según su ficha. Su archivo `model.safetensors` pesa **470.641.600 bytes (~470,6 MB)**; no confundir “MiniLM” con unas pocas decenas de MB. La ficha observada limita secuencia a **128 tokens**; partir fragmentos según el tokenizer (por ejemplo 80–110 tokens y solape pequeño), no enviar fragmentos de 512 tokens que se truncarían sin más.

- Preparación con Internet: descargar un snapshot fijado, tokenizer/configuración/pooling y **un solo formato de pesos**; no bajar simultáneamente safetensors, `.bin`, ONNX y OpenVINO. Revisión observada de la ficha: `e8f8c211226b894fcb81acc59f3b34ba3efd5f42` (revalidar al preparar el snapshot).
- Si el perfilado muestra exceso de memoria, evaluar ONNX/int8 local como alternativa, con validación de pooling/normalización/equivalencia. ONNX Runtime ya está instalado, pero **no** el artefacto cuantizado ni su integración; no se afirma que esté listo.
- Cargar rutas locales con `local_files_only=True`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, telemetría deshabilitada y prueba de red bloqueada. La ausencia de tokenizer/pesos es un error de preparación, no una razón para acceder al Hub en una consulta.
- Seleccionar una colección pequeña: artículos médicos open access con licencia de reutilización comprobada por documento, o material educativo con permiso. Verificar autor, título, versión, URL, licencia y SHA-256. No se ha aprobado ni indexado aún una colección; estar en PMC o accesible en web no implica permiso automático para copiar todo.
- Las seis categorías iniciales serán las del encargo; casos sintéticos **no** se indexan como evidencia médica. Conservar ficheros fuente en almacenamiento local, metadatos/textos/fragmentos en PostgreSQL y `vector(384)` con identificador de modelo/revisión.
- Búsqueda por coseno, top-k pequeño y filtro de versión/colección autorizada. Para pocos documentos basta búsqueda exacta; no empezar creando HNSW/infraestructura innecesaria. Ajustar el umbral de relevancia con consultas de evaluación, no inventarlo como “confianza clínica”.
- Si la colección está vacía o no hay fragmentos pertinentes, responder insuficiencia documental. Mostrar fuente y fragmento que realmente se recuperó; referencias del LLM deben pertenecer a la lista recuperada, nunca aceptar URLs inventadas.
- Recuperar/indexar con embeddings y luego liberar ese proceso antes de cargar el LLM. Detenerse al finalizar Fase 3, sin tocar frontend.

## 8. LLM, extracción y fusión — fases 4 y 5

Evaluar **`qwen2.5:1.5b` cuantizado** en Ollama CPU, contexto y salida acotados; no está instalado. No se descargó ni se midió su consumo. `qwen2.5:3b` existente no es la selección inicial de radiología con tan poca memoria libre.

- Solo después de visión y embeddings, y con RAM suficiente; descargar en preparación, comprobar presencia/digest antes de consultar y nunca invocar `pull` desde un endpoint.
- Extracción del informe preservando original y evidencia: presente/negado/incierto, localización, impresión y recomendaciones **expresadas**. Si un modelo omite/malinterpreta negaciones, fallar de forma conservadora, no inventar diagnóstico.
- Una capa determinista compara score/etiquetas con el informe estructurado; declarar discrepancias en vez de dejar al LLM resolverlas. Solo reconocer umbrales experimentales documentados y sin presentarlos como calibración clínica.
- Generación exclusivamente con el resultado estructurado y los fragmentos recuperados, delimitados como datos no confiables. Sin herramientas, SQL ni ejecución de órdenes dentro del informe/documentación. Validar secciones/citas y bloquear recomendaciones terapéuticas no solicitadas.
- Una revisión humana decide aceptación/rechazo; no modificar informe confirmado ni autor original. “Validado por médico” solo tras una acción explícita y autorizada, no tras finalizar una inferencia.
- Fallback obligatorio si Ollama falla o falta RAM: plantilla breve con scores experimentales, frases del informe, coincidencias/discrepancias, extractos documentales y referencias; no generar una interpretación no respaldada. Sin documentos, expresar insuficiencia aunque el LLM responda.

## 9. Integración y control de memoria — Fase 6

Extender **`imagenes`**, no abrir una aplicación separada ni usar un segundo monolito. Diseño modular propuesto: entidades/estados; casos de uso de análisis/revisión; puertos de visión, embeddings, recuperación, generador y almacenamiento; adaptadores locales/SQL; presentación HTTP. La base mínima de estudios/archivo/informe de Rayos X está pendiente, debe quedar expresamente incluida en esta fase o aportarse desde otra rama.

Endpoints propuestos, todavía no existentes:

- `POST /imagenes/ia/analisis` → 202 y job ID, con referencia a estudio/archivo/informe autorizado y clave idempotente.
- `GET /imagenes/ia/analisis/{id}` y `/fuentes` → solo usuarios autorizados sobre ese estudio.
- `POST /imagenes/ia/analisis/{id}/revision` → acción/motivo y profesional desde sesión, sin editar diagnósticos confirmados automáticamente.

Job persistido sencillo, un ejecutor controlado y sondeo con límites; no Redis/Celery. Inicialmente una instancia de backend/un ejecutor; si se amplía a varios procesos, la exclusión debe coordinarse entre ellos, no confiar en un semáforo local. Recuperar jobs interrumpidos a un estado explícito, no dejarlos “procesando” indefinidamente.

Visión → liberar trabajador → embeddings/RAG → liberar trabajador → LLM o plantilla. Procesos hijos controlados dentro del módulo permiten liberar memoria y aplicar un timeout real en Windows; **un timeout sobre `asyncio.to_thread` por sí solo no detiene una inferencia ni libera sus recursos**. No es un servidor o microservicio independiente. Definir el mecanismo más pequeño que permita cancelación real y un máximo global de una inferencia pesada, incluyendo conflictos con Whisper/Consulta Médica. Si otro proceso de IA está usando recursos, rechazar/posponer de forma recuperable; no apagar modelos ajenos sin autorización.

UI futura: lista/ficha de estudio, imagen original local protegida, informe/versiones y panel IA consistente con Laboratorio; distinguir scores visuales, contenido del informe, evidencia RAG y revisión médica. Mostrar progreso/error/fuentes/estado. La normalidad no se afirma y los scores no se muestran como porcentajes de certeza. Ningún cambio de frontend se hizo en Fase 1.

## 10. Offline: qué falta y cómo comprobarlo

No se hizo una prueba offline radiológica en esta fase porque los componentes todavía no existen. No confundir la inspección sin inferencia con una demostración de funcionamiento offline.

- Preparación explícita con conexión: wheels/lock compatible, artefactos/hashes/licencias, modelos, tokenizer, documentación y muestras desidentificadas autorizadas. Consultas posteriores no deben realizar ninguna de estas descargas.
- El código de TorchXRayVision consulta caché y descarga si falta: hay que neutralizar esa resolución en el adaptador de runtime. HF necesita flags offline **y** cargas locales. Ollama debe tener el modelo preparado. RAG consulta solo PostgreSQL local. No buscar URLs de las citas durante el análisis.
- El Whisper actual también puede descargar su modelo en la primera transcripción. Si la exigencia offline cubre **todos** los endpoints de SarcoSistema, habrá que preparar Whisper y añadir una política de carga solo local; no afirmar que hoy toda la aplicación impide descargas. La radiología no necesita invocarlo.
- Prueba real posterior: script local independiente de esta sesión de asistencia, con red externa deshabilitada por el usuario en una ventana acordada, preservando loopback y la red virtual de Docker/PostgreSQL. No deshabilitar ahora adaptadores ni firewall del usuario. Los mocks de red/flags son pruebas adicionales, **no** sustituyen esa prueba real.
- Verificar imagen válida/inválida, informe afirmativo/negado/incierto, discrepancia, corpus vacío, modelo ausente, memoria insuficiente, timeout y LLM caído. Comparar referencias con fragmentos/versiones guardados. Registrar tiempos/RAM y evidencias observadas sin datos clínicos reales.

## 11. Datos y evaluación — Fase 7

- Ampliar de una radiografía a **10–20** muestras reales de investigación con permisos/atribución/etiquetas verificadas, sin descargar paquetes completos. Las imágenes de prueba públicas de un repositorio no son automáticamente una evaluación independiente ni autorizan redistribución.
- **30–50** casos sintéticos con `synthetic=true`, procedencia y expectativas funcionales, sin fingir que etiquetas/estudios son pacientes auténticos. No usarlos como corpus médico.
- NIH ofrece imágenes y etiquetas, no debe suponerse que trae un informe auténtico emparejado para cada imagen. Si se combina una imagen real con un informe inventado, marcar explícitamente la simulación de integración.
- Con n pequeño solo describir salidas, tiempos, memoria, coincidencias por etiqueta y errores; no afirmar sensibilidad, especificidad ni precisión clínica fiables ni validación hospitalaria.

## 12. Archivos futuros previstos (no modificados ahora)

| Fase | Rutas previstas |
|---|---|
| 2 | `backend/requirements-radiologia.txt`; `backend/scripts/preparar_modelos_radiologia.py`; `backend/app/imagenes/{domain,application/ports,infrastructure/vision,tests}/`; ruta local de pesos/manifest fuera de git |
| 3 | `backend/scripts/indexar_documentos_radiologia.py`; `backend/app/imagenes/infrastructure/{embeddings,rag,persistence}/`; una revisión nueva en `backend/alembic/versions/`; carpeta local de documentos y manifest de fuentes |
| 4–5 | `backend/app/imagenes/application/use_cases/`; `infrastructure/llm/`; contratos/esquemas de extracción/fusión y pruebas |
| 6 | Implementación de `backend/app/imagenes/storage.py` y adaptadores; `presentation/router.py` conservando compatibilidad con `imagenes/router.py`; migración de análisis/revisión; `backend/app/config/settings.py`, `.env.example` y control compartido de recursos en `app/ia/` si procede |
| 6 | `frontend/src/features/imagenes/{api,pages,components,hooks}/`; `frontend/src/app/router.jsx`; enlace/permiso en Inicio; usar componentes/tokens compartidos sin cambiar negocio de Laboratorio |
| 7 | Fixtures sintéticos con procedencia, manifest de muestras reales externas, scripts de evaluación/offline y documentación reproducible |

No crear todos esos archivos de una vez. En Fase 2 bastan preparación, servicio visual y prueba CPU; los nombres concretos finales se acuerdan al ejecutar cada fase. No versionar imágenes/pesos grandes, secretos ni registros clínicos.

## 13. Comprobaciones realizadas ahora

- `git status --short --branch`: `main` y cambios locales previos conservados.
- CIM/WMI y disco: recursos de la sección 3, sin carga artificial ni inferencia.
- Inventario de dependencias por metadatos, sin importar runtimes pesados ni instalar paquetes.
- PostgreSQL: versión, extensión disponible/instalada, columnas vectoriales, tablas/columnas, roles, servicio/catálogo IMG, cabecera Alembic y conteos de informes/archivos, con consultas de solo lectura.
- Ollama: `/api/tags` y `/api/ps`; no `pull` ni generación.
- Rutas realmente registradas: `/ia/transcribir`, `/ia/transcriptor/registros`, detalle de registros y `/consultas/extraer-datos-clinicos`; **ninguna operación de imágenes/radiología**.
- `python -m pip check`: correcto.
- `python -m pytest -q`: **192 passed, 2 skipped** (no se habilitaron evaluaciones lentas de modelo).
- `npm test`: **22 passed**. `npm run lint` y `npm run build`: correctos.
- Solo se consultaron documentación/código y metadatos públicos online para planificación. No se enviaron informes, pacientes o imágenes a Internet y no se descargaron artefactos de inferencia.

**No realizados:** inferencia DenseNet, embeddings, RAG, Qwen 1.5B, prueba offline del nuevo flujo, latencia/RSS de modelos, precisión diagnóstica o visualización de un estudio real. No se inventan esos resultados.

## Fuentes técnicas consultadas

- TorchXRayVision: https://github.com/mlmed/torchxrayvision — README, `torchxrayvision/models.py`, `datasets.py` y LICENSE (rama upstream consultada, aún no una versión instalada/fijada).
- Metadatos de distribución: https://pypi.org/pypi/torchxrayvision/json
- Metadatos de pesos (sin descargar): https://api.github.com/repos/mlmed/torchxrayvision/releases/tags/v1
- Modelo de embeddings: https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 — ficha, dimensión, longitud máxima y metadatos de archivos.

**Cierre:** Fase 1 terminada. Antes de continuar, revisar este informe y el bloqueo actual de RAM; esperar autorización para la Fase 2. No se inicia automáticamente ninguna fase posterior.
