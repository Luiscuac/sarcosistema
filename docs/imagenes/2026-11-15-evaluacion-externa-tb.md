# Rayos X v2: evaluación externa con tuberculosis y asistente priorizado

Fecha: 15/11/2026 · rama `feat/rayos-x-ia-v2`. **No es validación clínica**: imágenes de investigación anonimizadas, sin datos de pacientes del hospital. La IA ordena, señala y avisa; no diagnostica ni publica.

## 1. Por qué una evaluación externa

El modelo `densenet121-res224-all` (TorchXRayVision 1.5.7) se entrenó con NIH, CheXpert, MIMIC, PadChest, OpenI, RSNA y Google. Evaluarlo con NIH sobreestima su rendimiento. Se usaron dos conjuntos que **no vio**, con la respuesta conocida (TB / normal):

| Conjunto (NLM/NIH) | Imágenes | TB | Normales | Formato |
|---|---|---|---|---|
| Shenzhen (China) | 662 | 336 | 326 | PNG **en paleta**, ~3000×3000 |
| Montgomery (EE. UU.) | 138 | 58 | 80 | PNG gris, **4892×4020 (19,7 MP)** |

Condiciones de NLM: no compartir el conjunto fuera del grupo de investigación (`.datasets/` no se versiona). Citas obligatorias:
- Jaeger S. et al. *Automatic tuberculosis screening using chest radiographs*. IEEE TMI 2014;33(2):233-45.
- Candemir S. et al. *Lung segmentation in chest radiographs using anatomical atlases with nonrigid registration*. IEEE TMI 2014;33(2):577-90.
- Regiones de lesión de Shenzhen: Yang F. et al. *Annotations of Lung Abnormalities in the Shenzhen Chest X-ray Dataset*. Data 2022;7:95.

Reproducir (desde `backend/`):
```powershell
.\.venv\Scripts\python.exe -m scripts.preparar_tb_nlm --descargar          # ~4,4 GB, reanudable, manifiesto SHA-256
.\.venv\Scripts\python.exe -m scripts.evaluacion_radiologia.tb_externa      # 18 scores por imagen + métricas
.\.venv\Scripts\python.exe -m scripts.evaluacion_radiologia.tb_sonda        # índice pulmonar + prueba de atajo
.\.venv\Scripts\python.exe -m scripts.evaluacion_radiologia.tb_mapas        # mapas de calor vs regiones de radiólogos
```

## 2. Hallazgos del sistema original (v1)

1. **Rechazaba 773 de 800 radiografías reales**: Shenzhen por estar en modo paleta y Montgomery por superar 16 MP. DICOM no se analizaba.
2. **Error de integración**: las imágenes que sube el rol Rayos X se guardaban en `storage/imagenes`, pero el visor del médico y la IA leían solo `.storage/radiologia`. Una radiografía subida desde la pantalla real no llegaba al médico.
3. Mostraba 3 de las 18 categorías que calcula el modelo; sin mapa de calor, sin control de calidad; la IA solo corría si el médico la pedía sobre un informe ya publicado.

## 3. Qué tan bien "ve" el modelo (sin etiqueta de TB)

AUC (0,5 = azar; 1 = separación perfecta), IC 95 % por bootstrap:

| Grupo | Promedio de categorías pulmonares | Mejor categoría sola |
|---|---|---|
| Todos (800) | 0,79 [0,76–0,82] | Neumotórax 0,86 |
| Shenzhen | 0,78 | Neumotórax 0,85 · Infiltrado 0,83 |
| Montgomery | 0,91 | Masa 0,93 · Nódulo 0,91 |
| Hombres / Mujeres | 0,82 / 0,75 | — |

Que "Neumotórax" sea el mejor indicador muestra que **los nombres de categoría no deben leerse literalmente** como hallazgos de TB: son señales de anormalidad. Mujeres rinden peor: debe vigilarse.

## 4. Índice pulmonar y la lección del atajo

| Variante (entrena en Shenzhen, prueba en Montgomery) | Shenzhen (CV) | Montgomery (externo) |
|---|---|---|
| Capa sobre 1024 características internas | 0,93 | **0,52** (azar) |
| **Combinación de las 18 categorías (índice v1)** | 0,86 | **0,92** [0,87–0,97] |

Las 1024 características permiten reconocer **el hospital de origen con AUC 1,0**: la capa aprendió el equipo de rayos X, no la TB (*aprendizaje por atajo*). La combinación de 18 categorías tiene pocos parámetros y sí generaliza; también distingue el hospital (0,996), por eso **lo que vale es la prueba externa**, no la interna.

El **umbral no se transfiere**: el punto que en Shenzhen detecta el 90 % de TB, en Montgomery marca casi todo (especificidad 0,05). El **orden sí se conserva**. Por eso el índice se usa para **ordenar la bandeja**, y los niveles alta/media/baja son provisionales (`RADIOLOGY_TRIAGE_UMBRAL_ALTA/MEDIA`) hasta calibrarlos con casos validados del propio hospital. Implicación para Fase 3: un fine-tuning con un solo hospital sería peligroso; requiere varios sitios y prueba externa.

## 5. Resultados v2 (pasando por el código de producción)

| | v1 | v2 |
|---|---|---|
| Radiografías rechazadas por producción | 773 / 800 | **0 / 800** |
| AUC promedio pulmonar, todos | 0,79 | 0,795 [0,76–0,82] |
| Shenzhen / Montgomery | 0,78 / 0,91 | 0,78 / 0,91 |
| Hombres / Mujeres | 0,82 / 0,75 | 0,82 / 0,75 |
| Índice pulmonar en Montgomery (externo) | — | **0,92** [0,87–0,97] |
| Segundos por imagen (modelo ya cargado) | 0,8 | 0,5 |

Reducir a 2048 px antes del preprocesamiento no cambia el rendimiento; ahora entran todas las imágenes.

## 6. ¿Los mapas de calor apuntan a la lesión?

*Pointing game* sobre 123 radiografías con TB y regiones de consenso (Grad-CAM hacia el índice):

| Medida | Shenzhen (68) | Montgomery (55) | Todos (123) |
|---|---|---|---|
| El **pico** cae dentro de una región | 10 % | 11 % | **11 %** |
| Azar (punto aleatorio en el área analizada) | 6 % | 3 % | 5 % |
| La **zona activa** toca una región | 63 % | 62 % | 63 % |
| Área media de la zona activa | 16 % | 20 % | 18 % |
| Picos en el tercio inferior (diafragma/abdomen) | 31 % | 25 % | 28 % |

Conclusión honesta: el mapa es **mejor que el azar pero no localiza lesiones de forma fiable**. La zona activa suele tocar la lesión porque es amplia, y casi un tercio de los picos cae en la parte baja (la TB predomina en lóbulos superiores). Por eso la interfaz lo muestra **apagado por defecto**, como "dónde se apoyó el modelo" y nunca como ubicación de lesión. Mejora futura: restringir el mapa a los campos pulmonares con un modelo de segmentación local y volver a medir con este mismo script.

### 6.1 v3: mapas limitados a los campos pulmonares

Segmentación anatómica local (PSPNet ChestX-Det de TorchXRayVision, safetensors verificado). El Grad-CAM se multiplica por la máscara pulmonar, dilatada, antes de normalizar:

| Medida (123 radiografías con TB) | Sin máscara | **Con máscara** |
|---|---|---|
| Pico dentro de la lesión (azar 5 %) | 10,6 % | **12,2 %** |
| Zona activa que toca la lesión | 62,6 % | **67,5 %** |
| Área media de la zona activa | 18 % | **10 %** |
| Picos en el tercio inferior | 28,5 % | **19,5 %** |

Mejora en las cuatro medidas: la zona es la mitad de grande y aun así toca la lesión más a menudo. Sigue siendo modesto, así que el mapa continúa apagado por defecto y con la misma advertencia. Costo: ~3 s y ~400 MiB más por estudio (pico ~930 MiB). Se activa con `RADIOLOGY_LUNG_MASK_ENABLED=true` cuando la segmentación está preparada. Si se detecta menos del 12 % de campo pulmonar, el control de calidad avisa que puede no ser un tórax frontal.

## 7. Qué cambió en el producto

| Antes | Ahora |
|---|---|
| Solo PNG/JPEG 8 bits ≤16 MP | PNG paleta/16 bits/RGBA, JPEG, ≤60 MP (reducción a 2048 px) y **DICOM** sin comprimir/RLE (MONOCHROME1, VOI LUT, metadatos) |
| El navegador no podía mostrar DICOM/16 bits | `GET /imagenes/analisis/estudios/{id}/archivos/{aid}/vista`: PNG generado localmente |
| 3 categorías | 18 ordenadas, marcadas sobre el punto técnico |
| Sin prioridad | Índice pulmonar con "qué lo eleva" (contribuciones) |
| Sin explicación visual | Mapas de calor Grad-CAM (índice y 3 categorías principales) con zona más activa |
| Sin control de entrada | Avisos: resolución baja, contraste, saturación, lateral/otra región/otra modalidad (DICOM) |
| IA tardía, a pedido | **Triaje automático al subir** (`imagen_triaje_ia`, migración `20261115_0017`); bandeja de Rayos X ordenada: urgentes, luego índice; refresco mientras analiza |
| Visor estático | Zoom, desplazamiento, brillo/contraste, invertir, capa de calor con opacidad |

Rendimiento medido (CPU i7-10750H): ~10 s por estudio de extremo a extremo (incluye arranque del trabajador efímero), pico ~535 MB de RSS; el Grad-CAM añade ~0,25 s.

## 7.1 v3: comparación del informe, evidencia, DICOM comprimido y calibración local

| Antes (v2) | Ahora (v3) |
|---|---|
| Informe comparado en 3 categorías | **18 categorías**, español e inglés, tolerante a tildes; negación, incertidumbre con alcance ("vs", "sugestiva de…"), frases de normalidad ("senos costofrénicos libres", "silueta cardíaca normal") |
| Solo discrepancias y coincidencias | Más **posible omisión**: el modelo destaca algo que el informe no menciona (máximo 5, ordenadas por score) |
| Corpus RAG: 2 artículos, 3 temas | 5 artículos de acceso abierto (CC BY / CC BY-NC-SA verificadas), incluidos signos radiográficos generales y TB; 18 temas + tuberculosis. Si falta respaldo, se abstiene |
| DICOM comprimido rechazado | JPEG Baseline/Lossless y JPEG 2000 con `pylibjpeg` local; JPEG-LS se rechaza con un mensaje claro |
| Umbrales provisionales sin forma de medirlos | El médico puede indicar "¿anormal?" al revisar (migración `20261116_0018`); el panel **Desempeño del asistente** muestra concordancia y, con ≥20 casos por clase, el AUC local y umbrales sugeridos (no se aplican solos) |

Extracción del informe (no es validación clínica):

| Conjunto | Extractor v2 | Extractor v3 |
|---|---|---|
| Corpus sintético original (300 informes, 3 categorías) | 80,7 % | 100 % |
| Corpus sintético ampliado (1800 informes, 18 categorías) | — | 100 %, sin menciones falsas |
| Frases redactadas como informes reales (22, escritas a mano) | — | 22/22 |

Los corpus sintéticos usan plantillas que también guiaron el diseño de las reglas, así que el 100 % es optimista. Informes reales con redacción libre pueden fallar; por eso la comparación se presenta como ayuda para revisar, nunca como conclusión.

## 8. Limitaciones

- Dos conjuntos públicos de TB; no representan la población ni los equipos del hospital.
- El modelo no tiene categoría de TB; el índice es un proxy de anormalidad pulmonar.
- Los mapas de calor muestran dónde se apoyó el modelo, no la ubicación confirmada de una lesión.
- DICOM comprimido (JPEG/JPEG 2000) aún no se admite: exportar sin compresión.
- Antes de usar niveles fijos, calibrar umbrales con casos validados localmente y revisar el rendimiento por sexo y edad.
