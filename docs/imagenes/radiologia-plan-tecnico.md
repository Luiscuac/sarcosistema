# Rayos X: análisis del sistema y plan técnico

> 16/11/2026. Complementa [radiologia-convencional-investigacion.md](radiologia-convencional-investigacion.md), el [catálogo](radiologia-convencional-catalogo.md) y el [contrato de API](radiologia-api.md).

## 1. Qué se reutiliza de Laboratorio

| De Laboratorio | Uso en Rayos X |
|---|---|
| Tablas `solicitud`, `estudio_solicitado`, `tipo_estudio`, `paciente`, `estudio_estado_historial`, `auditoria_accion` | Las mismas: una solicitud agrupa varios estudios; cada estudio conserva su estado, imágenes e informe |
| Búsqueda y registro de pacientes y médicos (`LaboratorioService`) | Mismos casos de uso, expuestos al rol de Rayos X |
| Diálogo "Nueva solicitud" (paciente → estudios → datos del pedido → confirmar), idempotencia por clave | Mismo recorrido; los estudios se configuran con lateralidad, protocolo y proyecciones |
| Bandeja con indicadores, pestañas pendientes/finalizadas, filtros y agrupación por solicitud | Mismo patrón y clases `lab-*` |
| Captura por plantilla, "Guardar borrador" explícito, resumen de pendientes, confirmación al publicar, aviso de cambios sin guardar | Mismo patrón, con apartados descriptivos en vez de valores numéricos |
| Informe imprimible A4 (`informe-solicitud.css`, `window.print()`) | Mismo mecanismo para vista previa, impresión y PDF |
| `Dialogo`, `ConfirmarAccion`, `NavegacionLab`, `LaboratorioTopbar`, `useAvisoCambiosSinGuardar`, notificaciones | Tal cual |
| Inmutabilidad de lo publicado (triggers) | El informe validado no se modifica; las correcciones son adendas |

No existe Caja ni Facturación en el proyecto: no se integra.

## 2. Qué había en Rayos X y qué cambia

| Antes | Ahora |
|---|---|
| Un solo estudio (`RX_TORAX`) | 35 estudios configurables en 8 categorías (`tipo_estudio.configuracion_radiologia`) |
| Solo el médico solicitaba desde la ficha | Además, recepción de Rayos X crea solicitudes como en Laboratorio |
| Sin lateralidad ni proyecciones | Por estudio: lateralidad, protocolo, proyecciones solicitadas y realizadas |
| Sin registro técnico | Adquisición: proyecciones realizadas, posición, calidad, repeticiones y parámetros opcionales |
| Archivos ligados a cada versión del informe; cada guardado creaba una versión | Imágenes ligadas al estudio y a su proyección; el borrador se edita en su sitio |
| Informe de texto libre | Informe estructurado por plantilla, con texto final revisable |
| El rol `rayos_x` redactaba y publicaba | `rayos_x` hace todo el flujo (recibe, adquiere, redacta y valida); el rol `radiologo` se eliminó |
| Sin correcciones posteriores | Adendas con autor, motivo y fecha |
| PDF adjunto sin semántica | Informe externo como entidad aparte, siempre rotulado como externo |
| El rol `rayos_x` podía publicar por la ruta anterior | La ruta anterior solo permite publicar Rayos X a `rayos_x` (rol único del flujo) |

Se conserva sin cambios: ecografía, la asistencia IA del médico (`/imagenes/analisis`), el triaje (ahora solo para tórax) y la consulta del médico desde la ficha del paciente.

## 3. Modelo de datos (migración `20261116_0019`, aditiva)

- `tipo_estudio.configuracion_radiologia` JSONB: región, lateralidad, proyecciones, protocolos y plantilla. Editable sin migraciones.
- `radiologia_estudio_detalle` (1:1 con el estudio): lateralidad, protocolo, proyecciones solicitadas, indicación, entrega.
- `radiologia_adquisicion` (1:1): registro técnico; `parametros` JSONB para kVp, mAs, etc.
- `radiologia_imagen`: vincula `archivo_imagen` con el estudio y la proyección.
- `radiologia_informe` (1:1 con `informe_imagen`): contenido estructurado, plantilla usada y control de edición concurrente.
- `radiologia_adenda`: histórica, protegida por trigger.
- `radiologia_informe_externo`: PDF externo con procedencia.
- Sin rol `radiologo`: la migración `20261117_0020` reasigna esos usuarios a `rayos_x` y elimina el rol.

No se crean tablas por tipo de radiografía ni se cambian los estados de `estudio_solicitado` (compartidos con Laboratorio). La **etapa** radiológica se deriva:

| Estado general | Condición | Etapa |
|---|---|---|
| `pendiente_muestra` | sin adquisición | Pendiente de realización |
| `pendiente_muestra` | adquisición iniciada | En adquisición |
| `resultado_en_preparacion` | sin contenido de informe | Pendiente de informe |
| `resultado_en_preparacion` | con contenido | Informe en borrador |
| `publicado` | sin entrega | Validado |
| `publicado` | con entrega registrada | Entregado |
| `no_realizado` | | No realizado |

`informe_imagen.descripcion_texto` sigue guardando el texto final: es lo que leen la consulta médica y la asistencia IA.

## 4. Roles

> Actualizado 17/11/2026: por decisión del usuario, **un solo rol se encarga de todo el flujo**: `rayos_x`.

| Rol | Puede |
|---|---|
| `rayos_x` (recepción, técnico e informante) | Todo el flujo: crear solicitudes, registrar adquisición, subir y retirar imágenes, adjuntar informe externo, marcar no realizado, redactar, guardar borrador, validar, agregar adendas, entregar y habilitar o deshabilitar estudios del catálogo |
| `medico` (solicitante) | Solicitar desde la ficha del paciente y ver los informes validados |

## 5. Reparto del trabajo

| Tarea | Responsable | Archivos |
|---|---|---|
| Catálogo, investigación, migración, reglas de dominio, contrato de API, cliente HTTP y layout | Claude | `backend/app/imagenes/domain/`, `alembic/versions/20261116_0019_*`, `docs/imagenes/radiologia-*`, `frontend/.../api/radiologiaApi.js` |
| Repositorio, rutas, autorización y pruebas del backend | Claude | `backend/app/imagenes/` |
| Panel, nueva solicitud, detalle de solicitud e historial del paciente | Codex | `frontend/src/features/rayos_x/gestion/` |
| Espacio de trabajo del estudio: adquisición, imágenes, informe y vista imprimible | Codex | `frontend/src/features/rayos_x/estudio/` |
| Rutas, solicitud desde la ficha del médico, integración y pruebas de principio a fin | Claude | `frontend/src/app/router.jsx` y puntos de unión |
