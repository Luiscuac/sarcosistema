# Manual de uso: Rayos X con asistente de IA

Para médicos y personal de Rayos X. El asistente **ordena, señala y avisa**; no diagnostica, no publica informes y no reemplaza la lectura del médico.

## 1. Flujo de trabajo

1. **Médico, en Consultas:** abrir la ficha del paciente, ir a la sección **Rayos X** y solicitar *Radiografía de tórax*. Marcar **Urgente** si corresponde.
2. **Rayos X, en su bandeja:**
   - Abrir el estudio y subir la radiografía. Se admiten PNG, JPEG y **DICOM**, incluido DICOM comprimido JPEG o JPEG 2000.
   - La IA la analiza sola en segundo plano. La tarjeta muestra *IA analizando…* y después el nivel de prioridad.
   - Escribir el informe y **publicarlo**. La IA no cambia el informe.
3. **Médico, en Rayos X:**
   - Abrir el estudio, o pulsar **Abrir con asistente IA** desde el informe del paciente.
   - Confirmar que es una radiografía de tórax frontal y pulsar **Analizar con IA local**. Tarda entre 10 y 30 segundos.
   - Revisar los resultados y guardar una **revisión explícita**.

## 2. Bandeja priorizada (Rayos X)

| Indicador | Significado |
|---|---|
| **Urgente** | Prioridad clínica marcada por el médico. Siempre va primero. |
| **Revisar primero · 87** | Índice pulmonar alto. Conviene informarlo antes. |
| **Prioridad media / baja** | Índice intermedio o bajo. **Un valor bajo no descarta enfermedad.** |
| **Patrón TB** (insignia morada) | Solo junto a prioridad media o alta: el patrón se parece a tuberculosis. Señal experimental; no cambia el orden y su ausencia no descarta TB. |
| **revisar calidad** | La imagen tiene avisos: baja resolución, contraste, lateral, otra región, etc. |
| **IA analizando…** | En cola local; la bandeja se actualiza sola. |

El selector **Ordenar** alterna entre *Prioridad* (urgentes primero, luego índice) y *Llegada*.

## 3. Pantalla del médico

- **Visor:**
  - Rueda del ratón para zoom; arrastrar para mover; doble clic para restablecer.
  - Brillo, contraste e invertir.
- **Mapa de calor** (apagado por defecto): muestra **dónde se apoyó el modelo**, no dónde está una lesión. El recuadro amarillo marca la zona más activa.
- **Índice de prioridad pulmonar (0–100)** con *Qué lo eleva*, las categorías que más pesan. Sirve para ordenar; no es una probabilidad ni un diagnóstico de tuberculosis.
- **Patrón compatible con tuberculosis** (recuadro morado, solo con prioridad media o alta): señal experimental entrenada con TBX11K. Con el ensamble de 7 modelos (v2), en hospitales externos detectó entre 48 % y 82 % de las TB y apareció en 5–26 % de radiografías sanas. Si aparece, considerar baciloscopía o GeneXpert; si no aparece, **no descarta TB**. Detalle en `2026-11-20-deteccion-tb.md`.
- **Calidad de la imagen:** avisos que conviene revisar antes de confiar en el análisis.
- **Hallazgos del modelo:** las 3 categorías principales y el desplegable con las **18**. Los *scores* son normalizados: 0,5 es el punto técnico del modelo, no un porcentaje de certeza.
- **Comparación con el informe:**
  - 🔴 **Discrepancia:** el informe niega algo que el modelo destaca.
  - 🟠 **Posible omisión:** el modelo destaca algo que el informe no menciona.
  - 🟢 **Coincidencia:** descrito en el informe y destacado por el modelo.
  - La lectura del informe es por reglas: puede equivocarse con redacciones poco habituales.
- **Evidencia documental:** citas de artículos locales de acceso abierto. Se abstiene si no hay respaldo suficiente.
- **Revisión médica:**
  - Aceptar, corregir o rechazar la propuesta, con motivo.
  - Opcionalmente, indicar **"¿la radiografía es anormal?"**. Esa respuesta permite medir y calibrar el asistente en el hospital.
  - Guardar no publica nada ni modifica el informe.

## 4. Desempeño del asistente y calibración

En Rayos X, el botón **Desempeño del asistente** muestra solo cifras agregadas, sin pacientes:
- revisiones;
- aceptaciones;
- avisos;
- lecturas médicas.

Con al menos **20 lecturas anormales y 20 normales** calcula el **AUC local** y sugiere umbrales para los niveles *alta* y *media*. Los umbrales **no se aplican solos**: el responsable técnico los copia en `backend/.env`:

```
RADIOLOGY_TRIAGE_UMBRAL_ALTA=0.xxx
RADIOLOGY_TRIAGE_UMBRAL_MEDIA=0.xxx
```

y reinicia el backend. Hasta entonces se usan umbrales provisionales fijados con datos de otro hospital (Shenzhen). Esos umbrales **no se transfieren** entre hospitales.

### Aviso de tuberculosis

Al revisar un análisis, el médico puede indicar **Tuberculosis: confirmada / descartada** (opcional). Solo debe
marcarlo cuando haya **baciloscopía, GeneXpert o cultivo**; si aún no hay resultado, deja "Sin resultado todavía" y
puede registrar una revisión nueva cuando llegue.

Con al menos **20 casos con TB confirmada y 20 con TB descartada** de la misma versión del aviso, el panel calcula el
AUC local y sugiere un corte (especificidad 90 %). Tampoco se aplica solo:

```
RADIOLOGY_TB_UMBRAL_COMPATIBLE=0.xxx
```

Se aplica a los **análisis nuevos** tras reiniciar el backend. Si cambia la versión del aviso (v1 sin ensamble, v2 con
ensamble), los casos de la otra versión no se mezclan en la calibración.

## 5. Lo que el asistente NO hace

- No diagnostica, no publica, no corrige el informe y no envía datos fuera del equipo.
- No cubre todas las patologías ni diagnostica tuberculosis: el aviso de patrón TB es experimental, solo avisa y nunca descarta; la confirmación es bacteriológica.
- Rinde algo peor en mujeres que en hombres (AUC 0,75 frente a 0,82 en la evaluación externa): hay que tenerlo presente.
- Los mapas de calor no localizan lesiones de forma fiable (ver la evaluación).

Detalles técnicos y métricas: [`2026-11-15-evaluacion-externa-tb.md`](2026-11-15-evaluacion-externa-tb.md). Instalación: [`puesta-en-marcha-rayos-x.md`](puesta-en-marcha-rayos-x.md).
