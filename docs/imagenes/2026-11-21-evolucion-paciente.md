# Comparación con la radiografía anterior del paciente (2026-11-21)

> No es validación clínica. Compara las **señales del asistente**, no la enfermedad. El médico compara las imágenes.

## 1. Motivo

En TB y neumonías el médico necesita saber si la placa de hoy está mejor o peor que la anterior; el tratamiento de
TB dura meses. Cada radiografía de tórax ya tiene su triaje automático guardado (`imagen_triaje_ia`), así que la
comparación no ejecuta modelos ni agrega tiempo de inferencia.

## 2. ¿Qué diferencia es real? Ruido de re-toma

Dos radiografías del mismo paciente nunca salen iguales (postura, distancia, exposición). Antes de señalar un cambio
se midió cuánto se mueven los números **solo por repetir la toma** (`scripts/evaluacion_radiologia/evolucion_ruido.py`):

- 2.672 radiografías nunca usadas para entrenar (Shenzhen, Montgomery, India DA+DB, TBX11K val), con preprocesamiento de producción.
- Cada una re-tomada 2 veces con perturbaciones pequeñas e independientes: rotación ±5°, escala ±5 %, desplazamiento ±3 %, gamma 0,85–1,15. Dos repeticiones.
- Tolerancia = percentil 95 de la diferencia absoluta entre re-tomas.

| Señal | Mediana | P90 | **Tolerancia (P95)** |
|---|---|---|---|
| Índice pulmonar (0–1) | 0,037 | 0,122 | **0,153** |
| Patrón TB v1 | 0,020 | 0,122 | **0,185** |
| Patrón TB v2 (ensamble) | 0,044 | 0,178 | **0,230** |
| 18 categorías | — | — | 0,03–0,15 según categoría |

Para dar escala, la diferencia mediana del índice entre placas con TB y sin TB es 0,326: la tolerancia es menos de la mitad.

Hallazgo importante para la bandeja: **el 12,8 % de las re-tomas cambia de nivel de prioridad** (alta/media/baja) y
el **5,7 % cambia el aviso de TB**, porque muchas placas están cerca de un corte. Un cambio de nivel por sí solo no es
un cambio clínico; por eso la comparación usa el valor y su tolerancia, no el nivel.

Resultado guardado en `backend/app/imagenes/infrastructure/vision/evolucion_v1.json`.

## 3. Qué muestra

`GET /imagenes/analisis/estudios/{id}/evolucion` (rol médico; mismo acceso que el estudio):

- Anteriores: radiografías de tórax del **mismo paciente**, con **informe publicado**, anteriores a este estudio (hasta 5), con triaje completado y archivo activo. Por estudio, la radiografía de mayor índice (igual que la bandeja).
- Comparación con la **más reciente**:
  - índice: `aumenta` / `disminuye` / `sin_cambio_claro` (|Δ| ≤ tolerancia);
  - patrón TB: `aparece` / `sigue` / `desaparece` / `sin_aviso`, solo si ambas usan la misma versión (v1 y v2 no son comparables);
  - hasta 3 categorías con cambio mayor a su tolerancia y por encima del punto de corte (0,5) en alguna de las dos;
  - aviso si alguna imagen tiene calidad a revisar.
- No devuelve nombres ni textos del paciente.

En la pantalla del médico aparece como recuadro azul "Comparado con la radiografía anterior". Si no hay anteriores, no se muestra.

## 4. Límites

- La re-toma es **simulada**: no hay pares reales del mismo paciente en los datos públicos usados. Cambios de equipo,
  de proyección (AP/PA) o de inspiración pueden mover más los números.
- "Sin cambio claro" no significa "igual". "Desaparece el aviso de TB" no descarta TB.
- Pendiente: validar con pares reales (por ejemplo, controles de tratamiento de TB del hospital, con confirmación bacteriológica).

## 5. Reproducir (desde `backend/`)

```
PYTHONIOENCODING=utf-8 .venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.evolucion_ruido
```
Requiere la caché `tb_cache.py` y los pesos XRV de los 7 modelos (ver `2026-11-20-deteccion-tb.md`).
