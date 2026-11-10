# Fase 5 — evaluación experimental Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Producir una evaluación reproducible separada de textos sintéticos, visión real, recuperación documental e integración, con comparación con/sin RAG y evidencia offline.
**Architecture:** Herramientas de evaluación optativas fuera del flujo clínico; reutilizar los adaptadores y contratos actuales. Congelar entradas, etiquetas y protocolo antes de inferir; guardar resultados crudos, denominadores, fallos y recursos. No cambiar el sistema evaluado para mejorar la nota.
**Tech Stack:** Python 3.12, pytest, TorchXRayVision CPU existente, MiniLM local, PostgreSQL/pgvector y Docker.
**Spec:** Solicitud de Fase5 y aprobación en conversación: NIH exploratorio, 300 textos (75 positivos, 75 negativos, 75 ambiguos y 75 contradictorios), evaluación separada, comparación emparejada y ejecución sin Internet. Sin validación clínica ni entrenamiento nuevo.

## Global Constraints
- Solo datos sintéticos o radiografías públicas desidentificadas con procedencia y permiso comprobados.
- No cambios de esquema, credenciales, historias clínicas existentes, modelos, umbrales ni heurísticas de producción.
- Conservar todos los cambios locales; sin commits/push ni limpieza destructiva. Trabajar en rama actual autorizada; aislar datos de prueba en base temporal.
- Descargas solo en preparación explícita; sin autenticar como el usuario, aceptar acuerdos por él, contratar servicios ni eludir restricciones.
- Pesos/datos reales/resultados voluminosos fuera de Git. Versionables: textos ficticios, protocolo, scripts, pruebas y resumen agregado.
- Sin entrenar ni ajustar umbrales sobre el conjunto evaluado. Umbral técnico actual 0,5 no es clínico ni probabilidad calibrada.
- No equiparar textos sintéticos a imágenes ni inventar informes auténticos emparejados.
- Bloquear salida de Internet del runtime con Docker; no desactivar adaptadores del host ni interrumpir servicios ajenos.

## Review Focus
- Etiqueta no mencionada o ausente del CSV no debe convertirse en negativo confirmado.
- Muestreo por resultados o ajuste sobre el test produce sesgo: fijar selección antes de inferir.
- Corpus/preguntas creados juntos producen evaluación circular: identificar origen y ausencia de revisión experta.
- Dobles, cachés y errores parciales no deben contarse como inferencia real o éxitos.
- Docker sin red externa no equivale a probar navegador ni desconectar físicamente Windows: precisar frontera comprobada.

## Estructura e interfaces
- `backend/scripts/evaluacion_radiologia/casos.py`: construir/validar corpus textual ficticio, sin imports de modelos.
- `backend/scripts/evaluacion_radiologia/metricas.py`: métricas puras y soporte explícito de valores desconocidos.
- `backend/scripts/evaluacion_radiologia/texto.py`, `visual.py`, `rag.py`: evaluadores independientes con salidas JSON.
- `backend/scripts/evaluar_radiologia.py`: CLI orquestador, ejecución secuencial y manifiesto de ejecución.
- `backend/scripts/preparar_evaluacion_radiologia.py`: preparación NIH explícita y acotada.
- `backend/app/imagenes/tests/test_evaluacion_*.py`: pruebas nodependientes de red/modelos por defecto.
- `docs/imagenes/evaluacion/casos-sinteticos.jsonl`, `preguntas-rag.json`: entradas y referencias congeladas.
- `docs/imagenes/fase-5-evaluacion.md`: protocolo, comandos, resultados, limitaciones y conclusiones.
- `backend/Dockerfile.imagenes-evaluacion-test`: runner offline, reutilizando enfoque del Dockerfile de integración existente.

### Task 1: Corpus y métricas sin modelos
**Interfaces:** `generar_casos() -> list[dict]`; `validar_casos(casos: list[dict]) -> None`; `clasificacion(referencia: list, prediccion: list) -> dict`.
- [ ] RED: tests exigen 300 IDs únicos, texto inequívocamente sintético, 75 casos por grupo, 25 por hallazgo/grupo y etiquetas explícitas independientes del extractor; no duplicar cambiando solo IDs/edad.
- [ ] Definir familias de lenguaje/alcance, contexto ficticio y referencias por los tres hallazgos. Positivo=descrito; negativo=negado; ambiguo incluye incierto/ambiguo/no_mencionado según texto; contradictorio=afirmación y negación del mismo hallazgo. Incluir los tres errores conocidos sin corregirlos.
- [ ] RED: métricas con matriz conocida, clases sin soporte, desconocidos excluidos, cero divisiones y scores no finitos rechazados. Reportar n total, n evaluable, omitidos y errores; AUROC solo si hay ambas clases, sin fabricar 0/1 cuando no se puede calcular.
- [ ] Implementar funciones puras y guardar corpus legible reproducible. GREEN: `python -m pytest app/imagenes/tests/test_evaluacion_casos.py app/imagenes/tests/test_evaluacion_metricas.py -q`.

### Task 2: Evaluación textual e integración emparejada
**Interfaces:** `evaluar_textos(casos: list[dict]) -> dict`; conservar referencia y predicción por ID.
- [ ] RED: evaluador llama extractor real; mide exactitud por estado, macro-F1, matriz, errores por grupo/familia y ejemplos concretos. Los errores del sistema no son fallos del runner: conservarlos como resultados.
- [ ] Evaluar comparación de scores controlados explícitamente sintéticos con textos para probar discrepancias; no atribuir estos scores al modelo visual.
- [ ] Comparar mismos casos/scores con RAG habilitado y sin RAG mediante adaptador de evaluación explícito, sin cambiar producción. Separar llamadas reales a integración de simulaciones contractuales.
- [ ] GREEN: pruebas del evaluador verifican emparejamiento de IDs, invariancia de scores/texto al cambiar RAG y ausencia de diagnósticos confirmados. Ejecutar evaluación y guardar JSON por caso.

### Task 3: Preparación y benchmark visual NIH
**Interfaces:** manifiesto JSON de imágenes con ID/paciente pseudónimo, origen, SHA256, vista, etiquetas y naturaleza débil; `evaluar_visual(manifest: Path, salida: Path) -> dict`.
- [ ] Inspeccionar fuentes oficiales NIH/Box y disponibilidad de descargas individuales sin registro/pago. Fijar objetivo exploratorio de 60 imágenes frontales de pacientes distintos, con representación positiva de los tres hallazgos y controles; no prometer balance exacto si no existe en la fuente.
- [ ] Congelar IDs/semilla/método antes de inferir y registrar que selección enriquecida no estima prevalencia poblacional. Presupuesto inicial máximo 500 MiB de imágenes, sin descarga del dataset completo ni archivos masivos para extraer pocas imágenes.
- [ ] Si no se obtienen suficientes imágenes, conservar n real y bloqueo; las dos fixtures existentes se reportan solo como smoke test, nunca como benchmark suficiente ni independiente.
- [ ] RED: integridad, duplicados/paciente, vista, etiquetas desconocidas, hashes, falta de clases y fallo de inferencia. Implementar preparación con flag `--descargar`, sin sobrescribir muestras existentes.
- [ ] Ejecutar visión CPU real secuencial con pesos locales existentes. Reportar por clase AUROC/AP cuando sean definibles, sensibilidad/especificidad/precisión/F1 al umbral técnico fijado, TP/FP/TN/FN, n, fallos y tiempo/RSS. Comparación con etiquetas débiles no confirma diagnósticos; advertir solapamiento posible con entrenamiento.
- [ ] GREEN de pruebas puras y ejecución real documentada; no imputar salidas para errores/archivos inaccesibles.

### Task 4: RAG y ablación documental
**Interfaces:** preguntas JSON con ID, texto, respondibilidad, documentos/secciones pertinentes y fragmentos de referencia; `evaluar_rag(preguntas: list[dict], salida: Path) -> dict`.
- [ ] Crear 40 preguntas congeladas: 24 respondibles según corpus existente, 8 fuera de corpus, 8 ambiguas; referencias revisadas contra contenido real, no contra lo recuperado por el sistema. Documentar autoría sintética/no experta.
- [ ] RED: pruebas de Recall@4/MRR por documentos/secciones, precisión de abstención, integridad de cita (texto exacto/offset/hash) y casos no respondibles excluidos del recall. Relevancia automática no equivale a fidelidad clínica.
- [ ] Ejecutar embeddings y pgvector reales en copia temporal; reportar cobertura por hallazgo, latencia y errores. Conservar consulta fija de la integración y medir su falta de adaptación en vez de reemplazarla silenciosamente.
- [ ] Comparar con/sin RAG sobre mismas entradas: cobertura de referencias verificables, abstención, latencia y conservación de scores/estados. Sin RAG=sin evidencia documental, no LLM nuevo; no afirmar aumento de precisión visual por añadir documentos.
- [ ] GREEN: pruebas del evaluador y ejecución real guardadas con manifiesto de corpus/modelo.

### Task 5: Ejecución integrada offline y cierre
- [ ] Preparar runner y dependencias online; preservar artefactos verificados montados en lectura. Ejecutar PostgreSQL temporal y backend/modelos en frontera sin salida externa (por ejemplo PostgreSQL y runner compartiendo namespace de contenedor `--network none`, sin puertos publicados).
- [ ] Ejecutar 300 textos, preguntas RAG y muestras visuales disponibles dentro de esa frontera. Reutilizar flujo API autenticado de `scripts/verificar_imagenes_offline.py` con datos ficticios nuevos en base temporal: imagen real, informe demo etiquetado, análisis, citas, revisión, idempotencia, conflicto409 e informe sin cambios.
- [ ] Verificar bloqueo de conexión externa real, configuración Docker, exit code y OOM. Guardar salidas en host antes de perder tmpfs; no declarar browser offline si solo se ejecutó ASGI.
- [ ] Medir CPU/hilos, RAM total/libre y pico RSS observado, disco de artefactos, latencia completa y de inferencia; reportar mediana/p95 solo con n suficiente y definición explícita. No retirar guardas de recursos.
- [ ] Ejecutar `python -c "import app.main"`, `python -m pip check`, suite backend predeterminada y pruebas optativas por separado; frontend test/lint/build si cambió frontend (no previsto).
- [ ] Revisión independiente acotada a evaluación y datos sintéticos; corregir sesgos/errores del evaluador, no optimizar producción sobre el test. Documentar omisiones y errores por nombre.
- [ ] Entregar informe con tablas separadas, denominadores, evidencia offline, límites de independencia, hardware, comparación con/sin RAG y conclusión sobre entrenamiento: no justificado por textos sintéticos ni un muestreo débil pequeño. No declarar Fase5 completa si benchmark visual u offline quedaron bloqueados.

## Seguimiento
Plan ejecutado tras aprobación del alcance. Tasks1–5 completas: evidencia nueva, no reutilizada de fases anteriores. Registro detallado y decisiones en `docs/imagenes/evaluacion/progreso.md`; informe `docs/imagenes/fase-5-evaluacion.md`; resumen agregado `docs/imagenes/evaluacion/resumen-resultados.json`. 300 textos,60 NIH derivados,40 preguntas y API real offline completados; revisión independiente y dos correcciones del evaluador verificadas. Suite final298aprobadas/11omitidas; RAG DB separadas3aprobadas. Sin validación clínica ni entrenamiento. Las casillas del protocolo conservan los pasos originales; el registro de ejecución es la evidencia de cumplimiento.
