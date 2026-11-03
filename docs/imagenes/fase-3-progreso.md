# Progreso — plan: docs/superpowers/plans/2026-11-03-rag-torax.md

- Ejecución inline autorizada; conservar main y cambios locales como en fases anteriores. Sin commits ni push.
- Ruling: MiniLM multilingüe sustituye E5 por alineación con el contexto maestro confirmado; 384 dimensiones, mean pooling y máximo 128 tokens, sin prefijos query/passage de E5. Riesgo: evaluar relevancia español/inglés con corpus real antes de aprobar recuperación.
- Ruling: Ollama se difiere a Fase 4 por instrucción posterior; esta fase produce evidencia estructurada, no generación clínica libre.
- Preflight Task1→Task2: vectores normalizados 384 y metadatos/hash comunes. Task2→Task3: fragmentos con sección y offsets verificables; no referencias inventadas.
- Recursos observados: 2,19 GiB RAM libre, 94,39 GiB disco libre. No cargar modelos en este estado sin nueva medición y margen explícito.
- Modelo candidato: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2; ficha oficial comprobada, Apache-2.0, 384 dimensiones, pooling medio, longitud 128. No descargado todavía.
- Dependencias detectadas: torch, huggingface_hub, pgvector, asyncpg disponibles; transformers/sentence_transformers ausentes.
- [ ] Tarea 1: corpus, contratos y embeddings.
- [ ] Tarea 2: persistencia pgvector.
- [ ] Tarea 3: respuesta estructurada con citas y abstención.
- [ ] Tarea 4: offline real, regresiones, revisión y documentación.

Avance parcial verificado:
- 13 pruebas corpus/embeddings/preparación aprobadas; 7 de respuesta extractiva aprobadas; prueba de corpus a fragmentos aprobada.
- Prueba real PostgreSQL RED por tabla ausente; aplicada migración incremental 20261103_0008 y prueba GREEN: 3 passed con rollback del fixture sintético. Se habilitó vector sin alterar tablas clínicas.
- Nuevos artículos candidatos verificados en XML Europe PMC: PMC6958895 (CC BY-NC-SA 4.0) y PMC4753987 (permite uso no comercial con atribución). Artículo PMC3632825 descartado por no encontrar permiso explícito en XML.
- Preparación de corpus/modelo, instalación opcional y construcción del contenedor iniciadas en segundo plano. No afirmar que finalizaron ni que el RAG offline pasó hasta recibir y comprobar sus resultados.
- Generador estructurado conserva texto de consulta y citas originales, no confirma hallazgos del paciente ni traduce automáticamente evidencia inglesa.

Actualización tras notificaciones de preparación:
- Dependencias opcionales instaladas; `pip check` sin conflictos. Hub/tokenizers cambiaron a versiones compatibles con Transformers; regresiones backend ejecutadas después.
- Modelo preparado, revisión `e8f8c211226b894fcb81acc59f3b34ba3efd5f42`, safetensors 448,84 MiB. Corpus local verificado: 2 documentos, 215 fragmentos; todavía NO se generaron sus embeddings reales.
- Primera construcción Docker falló por DNS del servidor de paquetes. Diagnóstico posterior en contenedor bridge: resolución pypi.org y HTTPS 200 correctos. Reintento sin cambiar versiones: construcción aprobada. No era evidencia de versión inexistente de SQLAlchemy.
- Regresión detectada: preparador médico exigía exactamente revisión 0007, rechazando la 0008. Dos pruebas existentes RED; se validó ascendencia Alembic en lugar de igualdad exacta, ambas GREEN. Cambio limitado necesario por nueva migración, sin ejecutar alta de cuentas.
- Suite backend posterior: 242 passed, 10 skipped (24,08 s); frontend 22 passed y lint correcto. Build frontend pendiente en esta fase.
- Recursos tras construir imagen: RAM libre **0,87 GiB**. Bloqueo de seguridad: NO ejecutar embeddings ni prueba offline real con este margen; mínimo configurado 2 GiB. No reducir el mínimo ni cerrar procesos ajenos. Solicitar liberar aplicaciones/modelos antes de continuar la medición y prueba.
- Pendientes: embeddings reales/ingesta corpus, relevancia/citas/abstención offline con PostgreSQL aislado, medición de RAM/tiempo, revisión independiente, guía y verificaciones finales. Fase NO terminada.

Reanudación autorizada antes de integrar Rayos X:
- Recursos frescos: 6,36 GiB RAM libre y 99,06 GiB disco. Red interna Docker `sarcosistema-rag-fase3-offline`; PostgreSQL temporal separado, sin montar volumen clínico.
- Primera prueba real offline indexó 215 fragmentos con el modelo local, falló después por memoria retenida. Se usa trabajador spawn efímero para embeddings con timeout 180 s y terminate/kill/join. No se redujo el mínimo general.
- Repetición con trabajador: 2 passed en 285 s, con dos documentos/215 fragmentos, citas literales y abstención fuera de dominio. Hallazgo manual: cita sobre CT/biopsia respondía indebidamente a limitaciones RX; test específico RED y filtro por oración/modalidad agregado. Nueva prueba offline de calidad en ejecución, sin afirmar todavía que pasó.
- Nuevo alcance solicitado por usuario: integración visual+RAG+revisión en Rayos X (denominada Fase 4 en solicitud actual), sin forzar LLM ni diagnósticos automáticos. Aún no implementada.

- Calidad offline posterior al filtro inicial: 2 passed en 348,20 s; consulta de limitaciones ahora devuelve información insuficiente en lugar de cita CT/biopsia. Hallazgos importantes de revisión independiente: comparaciones CT/RX ambiguas, preparación no reanudable y permiso XML demasiado genérico. Todos reproducidos RED→GREEN; 22 pruebas dirigidas aprobadas después y suite backend 248 passed, 10 skipped. Nueva repetición offline con estos cambios finales en curso.
- Final: minor (deferred): falta cobertura unitaria aislada de todos los caminos timeout/EOF/kill de embeddings; la prueba offline sí ejecuta hijos reales y liberación entre consultas.
- Final: minor (deferred): filtro de tratamiento por palabras no uniforme español/inglés; salida es extractiva y no genera recomendaciones, no tratarlo como barrera de seguridad exhaustiva.
- Diseño de integración escrito en docs/superpowers/specs/2026-11-03-rayos-x-integracion-design.md. Builder-check independiente: nothing important left. Estado: propuesta, aún sin implementación ni aprobación detallada. DB local confirmada sin informes/archivos (0/0); no existe página/router de Rayos X. Se requiere feature nueva dentro de SarcoSistema, no una aplicación independiente.

- Verificación offline FINAL posterior a revisión: **5 passed, 344,22 s**. Inspección confirma red internal=true, readonly=true, memoria 3 GiB, exit0 y sin OOM. Se detuvo solo el PostgreSQL temporal propio; no se tocaron volúmenes clínicos ni conectividad host.
- Tareas 1–4 verificadas para RAG en modo extractivo, con menores diferidos ya registrados. No afirmar pertinencia clínica general: consulta de limitaciones se abstiene y el corpus es reducido.
- Diseño de integración aprobado por usuario; plan docs/superpowers/plans/2026-11-03-rayos-x-integracion.md escrito y pendiente de confirmación de ejecución detallada. Aún no hay implementación UI/API clínica de Rayos X.
