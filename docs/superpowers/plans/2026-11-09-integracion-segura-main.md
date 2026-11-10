# Integración segura main / Rayos X — Implementation Plan

> Ejecución directa en el worktree existente, autorizada por el usuario tras revisar el informe. REQUIRED SUB-SKILL: executing-plans. Registro de tareas y evidencia; no autorización para main, push ni base real.

**Goal:** Conservar IA, Ecografía y Laboratorio mediante integración local verificable.
**Architecture:** Evaluar corrección aditiva posterior a la unión existente, conservando el historial distribuido de main. Reparar operaciones omitidas según contrato físico comprobado, nunca mediante stamp. Separar clínica de Ecografía y análisis médico en backend/frontend.
**Tech Stack:** Python 3.12, Alembic, PostgreSQL16/pgvector aislado, React, node:test.
**Spec:** Solicitud del usuario y `docs/integracion/2026-11-09-main-rayos-x-bloqueo.md` revisado por él.

## Global Constraints
- No push, modificaciones a main, stamp, downgrade ni acceso a base real.
- Conservar respaldo y cambios de colaboradores; sin elegir globalmente una rama.
- Solo datos ficticios en contenedores propios sin volúmenes existentes.
- No importar secretos locales, ni descargar modelos durante inferencia.

## Review Focus
- RAG aplicado con padre original: no omitir Laboratorio ni Ecografía.
- Historial reordenado de main: no repetir DDL ni versiones de plantillas.
- Esquema parcial/desconocido: error explícito y transacción revertida.
- Permisos separados imagenes/medico y rutas sin duplicados.
- Jobs, revisión append-only y carga local real conservados.

## 1. Migraciones (antes del merge)
- [x] Leer schema, grafos, DDL/DML y reproducir omisiones en plan Alembic.
- [x] Añadir pruebas RED de actualización desde historiales originales y reordenados.
- [x] Implementar revisión correctiva nueva y precondiciones sin editar revisiones distribuidas adicionalmente.
- [x] Probar en PostgreSQL aislado: vacío, Laboratorio parcial/completo, IA original, unión original, main Ecografía y main IA. Comparar esquema y datos ficticios pre/post y pgvector.
- [x] Documentar estrategia y limitaciones; detener ante incompatibilidad no demostrable.

### Evidencia y decisiones de migración
- RED observado: falta correctiva desde unión0012; esquema real de Ecografía omitido.
- RED adicional: presencia de columnas/formatos no garantiza nullability/unidades válidas; comprobaciones reforzadas y GREEN.
- RED con dos cabezas originales: Alembic rechaza el solapamiento antes de ejecutar correctiva.
- Ruling: conservar exactamente el padre ya distribuido en main, sin inventar otra reescritura; correctiva0013 materializa lo omitido. Para dos cabezas originales, el preparador completa primero la unión0012 usando una copia temporal del grafo original. Son upgrades reales, no stamp ni ediciones de tracking. Coste si se distribuyó otro grafo desconocido: detener y revisar sus metadatos antes de aplicar.
- 18 pruebas GREEN en PostgreSQL16/pgvector propio en loopback, sin volúmenes ni BD real: 13 estados de partida, grafo y cuatro casos incompatibles. Comparación de columnas, constraints, índices, vistas y triggers entre perfiles; datos ficticios publicados, corpus, análisis y revisión conservados; doble upgrade sin cambios.
- No se considera compatible una instalación arbitrariamente modificada a mano: las precondiciones rechazan contratos parciales conocidos; cualquier fallo requiere copia aislada, no ocultarlo con stamp.

## 2. Código
- [x] Merge local `origin/main` sin commit automático.
- [x] Resolver seis conflictos: trasladar jobs al router de análisis, separar páginas/estilos de Ecografía e IA, rutas y topbar compatibles, no restaurar sidebar obsoleto.
- [x] Revisar merges automáticos y colisión ports.py/ports/vision.py; añadir regresiones de composición/imports/permisos.

## 3. Seguridad
- [x] Desversionar .env raíz conservando copia local, ignorarlo y documentar rotación pendiente sin revelar valores.
- [x] Retirar del índice temporales y bytecode sin borrar copias locales; revisar artefactos Playwright y secretos del diff.

## 4. Verificación y entrega
- [x] Import/pip check/pytest contra BD aislada; Alembic y pgvector.
- [x] npm test/lint/build y flujos críticos de ambos roles.
- [x] Inferencia/embeddings/RAG/persistencia reales y offline con modelos locales disponibles; reportar límites.
- [x] Revisar diff, marcadores, índice y estado original; revisión independiente si procede.
- [x] Commit local de integración con conflictos resueltos y evidencia registrada; informe sin declarar verificaciones omitidas. Rama conservada local, sin push ni cambios a main.

### Revisión final y cierre
- Tres findings Important introducidos se reprodujeron (5 RED) y corrigieron: env.py respeta Config/conexión, las dos etapas ahora comparten transacción, huellas físicas verifican protecciones IA/RAG/incidencias. 23 GREEN de matriz y 398 passed/11 skipped de suite completa final.
- Ruling: conservar la política clínica publicada de main sin introducir ownership nuevo no acordado; la revisión identifica descargas globales al rol médico. Coste si esa política no es la deseada: acceso médico demasiado amplio. Se informa como decisión del equipo pendiente antes de publicación, no se declara resuelta.
- Ruling: detener solo el contenedor propio de la matriz tras respaldar integration_suite ficticia, liberando sus 2.14GiB tmpfs; ninguna base real tocada. Coste: los demás estados ficticios temporales se recrean ejecutando la matriz, no se conservan tras detener tmpfs.
- Inferencia offline final: primer intento rechazado por recursos, segundo GREEN tras liberar matriz, sin bajar umbrales. Modelos, corpus y código montados readonly, red Docker none; cuatro citas y revisión persistida.
- Revisión independiente realizada una vez; no segunda revisión tras fixes, verificados con regresiones y suite. Sin minors adicionales informados.
