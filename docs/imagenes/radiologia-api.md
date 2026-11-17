# API de radiología convencional (contrato)

Prefijo: `/imagenes/radiologia`. Todas las rutas exigen JWT Bearer. Cliente frontend: `frontend/src/features/rayos_x/api/radiologiaApi.js`.

Roles: **T** = `rayos_x` (a cargo de todo el flujo: recepción, adquisición, informe y validación), **M** = `medico` (solicitante). El rol `radiologo` fue eliminado (migración `20261117_0020`).
Solo **R** redacta y valida informes. **T** nunca valida.

Errores: `{"detail": "mensaje"}` con 400 (regla incumplida), 403, 404, 409 (conflicto de estado o de versión), 413, 415, 422.
Cuando faltan requisitos, 409 devuelve `{"detail": {"mensaje": "...", "pendientes": ["..."]}}`.

## Objetos

### `Config` (configuración del estudio; viene del catálogo)

```json
{
  "version": 1, "categoria": "extremidad_inferior", "region": "Rodilla", "descripcion": "",
  "requiere_lateralidad": true, "permite_bilateral": true, "detalle_requerido": "",
  "proyecciones": [{"codigo": "AP", "nombre": "Anteroposterior (AP)"}],
  "protocolos": [{"codigo": "AP_LAT", "nombre": "AP y lateral", "proyecciones": ["AP", "LAT"]}],
  "plantilla": {
    "codigo": "articulacion", "nombre": "Articulación periférica", "version": 1,
    "generales": [{"clave": "tecnica", "titulo": "Técnica", "tipo": "texto", "ayuda": "...", "frases": ["..."]}],
    "apartados": [
      {"clave": "alineacion", "titulo": "Alineación ósea y relaciones articulares", "tipo": "texto", "ayuda": "...", "frases": ["..."]},
      {"clave": "angulo_cobb", "titulo": "Ángulo de Cobb", "tipo": "medicion", "unidad": "°", "minimo": 0, "maximo": 120, "ayuda": "..."},
      {"clave": "metodo", "titulo": "Método", "tipo": "opcion", "opciones": ["Greulich y Pyle", "Otro"], "ayuda": ""}
    ]
  },
  "fuente": "...", "notas": ["..."]
}
```

- `generales` siempre trae, en este orden: `tecnica`, `indicacion`, `comparacion`, `limitaciones`, `conclusion`, `recomendaciones`.
- `tipo`: `texto` (textarea), `medicion` (número con `unidad`, `minimo`, `maximo`), `opcion` (selector con `opciones`).
- `frases`: sugerencias que **solo se insertan si el médico pulsa**; nunca se rellenan solas. `conclusion` no trae frases.
- `detalle_requerido`: si no está vacío, es la etiqueta de un texto corto adicional de la solicitud (`detalle_region`).

### `EstudioFila`

```json
{
  "estudio_id": 12, "referencia_estudio": "RX-261116-AB12CD-1F2E", "solicitud_id": 7, "referencia_solicitud": "RX-261116-AB12CD",
  "paciente_id": 3, "paciente_nombre": "Paciente FICTICIO", "paciente_documento": "1234567",
  "tipo_estudio_codigo": "RX_RODILLA", "tipo_estudio_nombre": "Radiografía de rodilla", "categoria": "extremidad_inferior",
  "lateralidad": "derecha", "prioridad": "urgente", "estado": "pendiente_muestra",
  "etapa": "pendiente_realizacion", "etapa_texto": "Pendiente de realización",
  "fecha_solicitud": "2026-11-16T14:00:00Z", "medico_solicitante": "Dr. FICTICIO", "imagenes": 0, "triaje": null
}
```

- `etapa`: `pendiente_realizacion` → `en_adquisicion` → `pendiente_informe` → `borrador` → `validado` → `entregado`; además `no_realizado` y `anulado`.
- `estado` es el estado general heredado (`pendiente_muestra`, `resultado_en_preparacion`, `publicado`, `no_realizado`, `invalidado`); la interfaz debe usar `etapa`.
- `lateralidad`: `derecha` | `izquierda` | `bilateral` | `null`. `prioridad`: `urgente` | `sin_prioridad`.
- `triaje` (solo tórax con IA habilitada): `{estado, indice, nivel, calidad, contribuciones, radiografias}` o `null`.

### `EstudioDetalle`

```json
{
  "estudio": { "...EstudioFila": "...",
    "detalle": {"lateralidad": "derecha", "protocolo_codigo": "AP_LAT", "proyecciones_solicitadas": ["AP", "LAT"],
                "indicacion_clinica": "Dolor tras caída", "observaciones": null, "detalle_region": null,
                "motivo_no_realizado": null, "entregado_en": null, "entregado_a": null} },
  "paciente": {"id": 3, "nombre_completo": "...", "numero_documento": "...", "codigo_paciente": "...", "fecha_nacimiento": "1990-01-01", "sexo": "F", "edad": 36},
  "solicitud": {"id": 7, "referencia": "...", "fecha_solicitud": "...", "prioridad": "urgente", "procedencia": "este_centro",
                "medico_solicitante": "Dr. FICTICIO", "establecimiento": null, "diagnostico_principal": null},
  "config": { "...Config": "..." },
  "adquisicion": null,
  "imagenes": [{"id": 5, "archivo_id": 44, "nombre_original": "rodilla_ap.png", "mime_type": "image/png", "tamano_bytes": 120000,
                "hash_sha256": "...", "fecha_carga": "...", "proyeccion_codigo": "AP"}],
  "informe": null,
  "adendas": [{"id": 1, "motivo": "...", "texto": "...", "autor_nombre": "...", "registro_profesional": null, "fecha_hora": "..."}],
  "informes_externos": [{"id": 2, "nombre_original": "informe.pdf", "mime_type": "application/pdf", "tamano_bytes": 90000,
                         "establecimiento": "Centro externo", "profesional": null, "fecha_informe": "2026-11-10", "observaciones": null, "fecha_carga": "..."}],
  "historial": [{"fecha_hora": "...", "tipo": "estado", "descripcion": "Pendiente de realización", "usuario": "tecnico1"}],
  "pendientes": {"adquisicion": ["Adjunta al menos una imagen."], "validacion": ["Redacta la conclusión o impresión diagnóstica."]},
  "permisos": {"registrar_adquisicion": true, "gestionar_imagenes": true, "redactar_informe": false, "validar": false,
               "agregar_adenda": false, "adjuntar_externo": true, "marcar_no_realizado": true, "entregar": false}
}
```

`adquisicion` (o `null` si no se inició):

```json
{"estado": "en_proceso", "proyecciones_realizadas": ["AP", "LAT"], "lateralidad_realizada": "derecha",
 "posicion_paciente": "decubito_supino", "fecha_hora_adquisicion": "2026-11-16T15:10:00Z", "operador_nombre": "Téc. FICTICIO",
 "calidad": "adecuada", "limitaciones": null, "repeticiones": 0, "motivo_repeticion": null,
 "parametros": {"kvp": 60, "mas": 5, "tiempo_ms": 20, "indice_exposicion": 250, "indice_desviacion": 0.3, "dap": 12.5, "distancia_cm": 100, "equipo": "Sala 1"},
 "observaciones": null, "completada_en": null}
```

- `estado`: `en_proceso` | `completada`. `posicion_paciente`: `bipedestacion` | `sedestacion` | `decubito_supino` | `decubito_prono` | `decubito_lateral`.
- `calidad`: `adecuada` | `limitada` | `no_diagnostica`. Todos los `parametros` son opcionales.

`informe` (o `null`):

```json
{"id": 31, "numero_version": 1, "estado": "borrador", "estructurado": true, "plantilla_codigo": "articulacion",
 "contenido": {"generales": {"tecnica": "...", "conclusion": "..."}, "apartados": {"alineacion": "...", "angulo_cobb": 12}},
 "texto": "INDICACIÓN CLÍNICA:\n...", "texto_personalizado": false, "version_edicion": 3,
 "responsable_nombre": null, "registro_profesional": null, "fecha_hora_publicacion": null}
```

- `estado`: `borrador` | `publicado` (validado, inmutable). `estructurado: false` = informe antiguo de texto libre (`contenido` vacío, usar `texto`).
- `texto` es el informe compuesto (o editado por el médico si `texto_personalizado`).
- `permisos` ya considera rol y estado: la interfaz solo muestra las acciones permitidas, sin recalcular reglas.

## Rutas

| Método y ruta | Rol | Entrada | Salida |
|---|---|---|---|
| `GET /catalogo` | T, R, M | `?todos=true` (solo R: incluye inactivos) | `{categorias: [{codigo, nombre}], estudios: [{id, codigo, nombre, activo, config}]}` |
| `PATCH /catalogo/estudios/{tipo_estudio_id}` | R | `{activo: bool}` | `{id, codigo, nombre, activo, config}` |
| `GET /pacientes?termino=` | T, R | mínimo 2 caracteres | `[{id, nombre_completo, numero_documento, codigo_paciente, fecha_nacimiento, sexo}]` |
| `POST /pacientes` | T | igual que `POST /laboratorio/pacientes` | paciente creado (201) |
| `GET /medicos?termino=` | T, R | | igual que `GET /laboratorio/medicos` |
| `POST /solicitudes` | T, M | `SolicitudNueva` | 201 `{solicitud_id, referencia, estudios: [{estudio_id, referencia}]}` |
| `GET /estudios?vista=activos\|finalizados` | T, R | `activos` = no validados; `finalizados` = validados, entregados, no realizados | `EstudioFila[]` |
| `GET /solicitudes/{solicitud_id}` | T, R | | `{solicitud: {...}, paciente: {...}, estudios: EstudioFila[]}` |
| `GET /pacientes/{paciente_id}/estudios` | T, R | | `{paciente: {...}, estudios: EstudioFila[]}` |
| `GET /estudios/{estudio_id}` | T, R; M solo si está validado (como en el historial del paciente) | | `EstudioDetalle` |
| `PUT /estudios/{estudio_id}/adquisicion` | T | campos de `adquisicion` (sin `estado` ni `completada_en`) | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/adquisicion/completar` | T | — | `EstudioDetalle` (409 con `pendientes`) |
| `POST /estudios/{estudio_id}/imagenes` | T | multipart: `archivos` (1..10; JPEG, PNG o DICOM) y `proyecciones` (un valor por archivo, `""` = sin asignar) | `EstudioDetalle` |
| `PATCH /estudios/{estudio_id}/imagenes/{imagen_id}` | T | `{proyeccion_codigo: "AP" \| null}` | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/imagenes/{imagen_id}/retirar` | T | `{motivo}` (obligatorio) | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/no-realizado` | T | `{motivo}` | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/informe/vista-previa` | R | `{contenido}` | `{texto}` (composición oficial, sin guardar) |
| `PUT /estudios/{estudio_id}/informe/borrador` | R | `{contenido, texto_final: str \| null, version_edicion: int \| null}` | `EstudioDetalle` (409 si otro guardó antes) |
| `POST /estudios/{estudio_id}/informe/validar` | R | `{version_edicion, responsable_nombre, registro_profesional?, confirmo: true}` | `EstudioDetalle` (409 con `pendientes`) |
| `POST /estudios/{estudio_id}/adendas` | R | `{motivo, texto, autor_nombre, registro_profesional?}` (solo informe validado) | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/informes-externos` | T, R | multipart: `archivo` (PDF), `establecimiento`, `profesional?`, `fecha_informe?` (AAAA-MM-DD), `observaciones?` | `EstudioDetalle` |
| `POST /estudios/{estudio_id}/informes-externos/{externo_id}/retirar` | T, R | `{motivo}` | `EstudioDetalle` |
| `GET /informes-externos/{externo_id}/archivo` | T, R; M si está validado | | PDF |
| `POST /estudios/{estudio_id}/entregar` | T | `{entregado_a}` (solo validado) | `EstudioDetalle` |

Binarios de imágenes (rutas existentes, con autorización reforzada): `GET /imagenes/archivos/{archivo_id}` (original) y `GET /imagenes/archivos/{archivo_id}/vista` (PNG de 8 bits; usar siempre para DICOM).

### `SolicitudNueva`

```json
{
  "paciente_id": 3, "prioridad": "sin_prioridad", "procedencia": "este_centro",
  "medico_solicitante_id": 9, "medico_solicitante_nombre": null, "establecimiento_solicitante_nombre": null,
  "diagnostico_principal": "Gonalgia derecha", "clave_idempotencia": "uuid",
  "estudios": [
    {"tipo_estudio_id": 41, "lateralidad": "derecha", "protocolo": "AP_LAT", "proyecciones": ["AP", "LAT"],
     "indicacion": "Dolor tras caída", "observaciones": null, "detalle_region": null}
  ]
}
```

- `procedencia`: `este_centro` (exige `medico_solicitante_id`) u `otro_centro` (exige `establecimiento_solicitante_nombre` y `medico_solicitante_nombre`). Para **M** el solicitante es siempre el propio médico.
- `estudios`: 1 a 15. `lateralidad` obligatoria si `config.requiere_lateralidad`; `bilateral` solo si `config.permite_bilateral`. Si `proyecciones` va vacío se usan las del `protocolo`. No se repite el mismo estudio con la misma lateralidad.
- Reintentar con la misma `clave_idempotencia` devuelve la misma solicitud.

### Reglas que la interfaz debe respetar

- Las proyecciones **solicitadas** no se copian a las **realizadas**: el técnico marca lo que realmente adquirió (se puede ofrecer un botón "Usar las solicitadas").
- Imágenes y adquisición se editan mientras el informe no esté validado. Retirar una imagen exige motivo y no la borra.
- El informe se guarda con un botón explícito "Guardar borrador" (como Laboratorio); avisar de cambios sin guardar con `useAvisoCambiosSinGuardar`.
- Al validar se muestra un resumen y una confirmación explícita; después el informe es inmutable y solo admite adendas.
- Un informe externo se muestra siempre rotulado como "Informe externo" con su establecimiento; nunca como informe del sistema.
