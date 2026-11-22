# Detección experimental de tuberculosis (2026-11-20)

> No es validación clínica. El asistente no diagnostica TB: solo avisa de un patrón compatible y nunca la descarta.
> La confirmación es bacteriológica (baciloscopía, GeneXpert, cultivo).

## 1. Motivo

El modelo de producción (TorchXRayVision `densenet121-res224-all`) tiene 18 categorías y **ninguna es tuberculosis**.
El índice pulmonar v1 separa bien radiografías con TB de radiografías sanas en hospitales externos (ver
`2026-11-15-evaluacion-externa-tb.md`), pero no distingue TB de otras enfermedades pulmonares. En Bolivia la TB es
frecuente; un aviso específico tiene valor clínico si no genera demasiadas falsas alarmas.

## 2. Datos

| Fuente | País | Uso | TB | Sin TB |
|---|---|---|---|---|
| TBX11K train (Liu et al., CVPR 2020; CC BY 4.0) | China | Entrenamiento | 600 | 3.000 sanas + 3.000 enfermas no TB |
| TBX11K val | China | Elegir corte y épocas | 200 | 800 + 800 |
| Shenzhen (Jaeger 2014) | China, otro hospital | Prueba externa | 336 | 326 |
| Montgomery (Jaeger 2014) | EE. UU. | Prueba externa | 58 | 80 |
| DA+DB (Chauhan 2014), incluidos en TBX11K | India | Prueba externa | 22 | 50 |

- Las 400 copias de Shenzhen/Montgomery que trae TBX11K (`imgs/extra/mc+shenzhen`) se excluyen del entrenamiento.
- El grupo de prueba oficial de TBX11K no tiene etiquetas públicas y no se usa.
- Todas las imágenes pasan por el **preprocesamiento de producción** (`tb_cache.py`).
- Los datos quedan en `backend/.datasets/` (fuera de Git) y no se despliegan.

Etiquetas de Google sobre NIH (Majkowska 2019, Nabulsi 2021) se descargaron pero **no se usan para evaluar**:
el modelo base se entrenó con ellas (`torchxrayvision/datasets.py`, `NIH_Google_Dataset`), lo que inflaría los resultados.

## 3. Intentos (todos, incluidos los descartados)

AUC (0,5 = azar, 1 = perfecto). Externos = hospitales nunca usados para entrenar ni elegir cortes.

| # | Método | Validación TBX11K | Shenzhen | Montgomery | India | Decisión |
|---|---|---|---|---|---|---|
| 0 | Índice pulmonar v1 (producción, sin cambios) | 0,815 | 0,875* | **0,923** | **0,963** | Se mantiene |
| 1 | Cabeza lineal sobre 1024 características, solo TBX11K | 0,946 | 0,770 | 0,836 | 0,887 | Descartado: aprende el hospital |
| 2 | Ajuste parcial (denseblock4) en GPU, solo TBX11K | 0,983 | 0,775 | 0,759 (sens 0,10) | 0,876 | Descartado |
| 3 | Ajuste parcial, TBX11K + 80 % Shenzhen | 0,983 | 0,921 (20 % reservado) | 0,800 | 0,912 | Descartado: aún peor que el índice |
| 4 | "Deja un sitio fuera" con 18 salidas / 1024 / PCA | — | 0,66–0,70 | 0,64–0,88 | 0,88–0,92 | Descartado |
| 5 | Logística 18 salidas, TB vs enfermos no TB | 0,929 (TB vs otra enf.) | — | — | — | **Descartado en prueba de punta a punta**: marcaba TB en 84 % de sanas de TBX11K y 52 % de Montgomery |
| 6 | **Logística 18 salidas, TB vs todo lo demás** (`patron_tb_v1`) | 0,911 | 0,701 | 0,828 | 0,941 | **Integrado como aviso** |

\* El índice v1 se ajustó con Shenzhen: su cifra allí no es externa.

Conclusión: con cuatro fuentes y una GPU de 8 GB, **re-entrenar el modelo de imagen no supera al índice** al cambiar de
hospital (memoriza el hospital de origen). Lo que sí aporta es un aviso ligero de patrón TB basado en las 18 salidas.

## 4. Aviso integrado: `patron_tb_v1`

- Artefacto: `backend/app/imagenes/infrastructure/vision/patron_tb_v1.json` (coeficientes, corte y métricas; generado
  por `scripts/evaluacion_radiologia/tb_patron.py`). No agrega pesos, memoria ni tiempo de inferencia.
- Corte `compatible`: especificidad 90 % frente a todo lo no TB en TBX11K val.
- Se muestra **solo si la prioridad del índice es media o alta**, como "Patrón compatible con tuberculosis" en el
  veredicto del asistente y como insignia "Patrón TB" en la bandeja de Rayos X. **No cambia el orden de la bandeja.**
- Sin aviso **no** significa sin TB; la interfaz lo dice.

Frecuencia del aviso (aviso + prioridad media/alta, con el módulo del sistema):

| Grupo | TB con aviso | Sanas con aviso | Otras enfermedades con aviso |
|---|---|---|---|
| TBX11K val | 74 % | 6 % | 14 % |
| Shenzhen | 29 % | 6 % | — |
| Montgomery | 71 % | 21 % | — |
| India (DA+DB) | 91 % | 24 % | — |

Lectura honesta: el corte **no se transfiere entre hospitales** (en Shenzhen se le escapan 7 de cada 10 TB; en
Montgomery e India marca 1 de cada 4-5 sanas). Por eso solo avisa, nunca descarta, y debe calibrarse con casos locales.

## 5. Ensamble para el patrón TB (v2)

Se probó promediar las 18 salidas del modelo base con las de los 6 especialistas oficiales de TorchXRayVision
(nih, pc, chex, rsna, mimic_nb, mimic_ch; `tb_ensamble.py`). Candidatos fijados antes de mirar: modelo base solo o
los 7 juntos (también se informa cada modelo por separado y "solo especialistas").

| | Base solo | 7 juntos |
|---|---|---|
| Índice (anormalidad), Montgomery / India | **0,918 / 0,954** | 0,811 / 0,873 |
| Patrón TB, Shenzhen / Montgomery / India | 0,701 / 0,828 / **0,941** | **0,813 / 0,869** / 0,893 |
| Aviso TB (TB detectadas / sanas con aviso), Shenzhen | 29 % / 6 % | **48 % / 5 %** |
| Aviso TB, Montgomery | 71 % / 21 % | 60 % / **8 %** |
| Aviso TB, India | 91 % / 24 % | 82 % / 26 % |

Decisión: **el índice y las 18 categorías siguen con el modelo base**; **el patrón TB usa el ensamble** (`patron_tb_v2.json`)
si está preparado (`scripts.preparar_ensamble_radiologia --descargar`: safetensors verificados, pickle borrado). Sin
ensamble, el sistema usa `patron_tb_v1.json`. Coste medido en CPU (trabajador real, con mapas): +2,4-2,6 s por estudio,
+6 MiB de RSS. El valor de producción coincide con la evaluación (p. ej. MCUCXR_0104_1: 0,919 en ambos).

## 5b. Intentos del 2026-11-21: solo pulmones y mayor resolución (descartados)

Hipótesis: el ajuste fallaba en hospitales externos porque el modelo reconoce el hospital por bordes, letras y
colimación. Se recortaron las 9.272 imágenes a los pulmones con la segmentación local (0 fallos;
`tb_cache_pulmones.py`): **recorte** (rectángulo pulmonar) y **máscara** (además, fuera de los pulmones en negro).
También se probó un modelo de mayor resolución, ResNet50 XRV a 512 px (`tb_cache512.py`, `tb_variantes.py`).
Mismo protocolo que arriba. AUC en hospitales externos:

| Método | Shenzhen | Montgomery | India | Decisión |
|---|---|---|---|---|
| **Producción: patrón TB v2 (ensamble)** | **0,813** | **0,869** | **0,893** | Se mantiene |
| Patrón 18 salidas, placas recortadas | 0,760 | 0,814 | 0,802 | Descartado |
| Patrón 18 salidas, placas con máscara | 0,781 | 0,839 | 0,832 | Descartado |
| Ajuste parcial (GPU), placa completa (intento 2) | 0,775 | 0,759 | 0,876 | Ya descartado |
| Ajuste parcial, placas recortadas | 0,801 | 0,747 | 0,819 | Descartado |
| Ajuste parcial, placas con máscara | 0,788 | 0,723 | 0,865 | Descartado |
| Patrón 18 salidas, ResNet50 512 px | 0,867 | 0,758 | **0,545** | Descartado: inestable entre hospitales |
| Patrón 18 salidas, DenseNet base + ResNet 512 | 0,683 | 0,849 | 0,925 | Descartado: no mejora |

Índice (anormalidad) con placas recortadas o a 512 px: peor en Montgomery e India que el actual.

Lectura: quitar bordes y letras **no** resuelve la caída entre hospitales, así que la causa no es solo el "atajo
visual" del hospital; pesan las diferencias de población, equipos y criterio de etiqueta entre sitios. La mayor
resolución tampoco ayuda con estos datos. El ResNet 512 además se entrenó con VinDr, lo que impediría usar VinDr
como prueba externa. Con los datos disponibles, el siguiente salto real requiere **más hospitales distintos con TB**.

## 6. Pendiente

1. **VinDr-CXR** (Vietnam, PhysioNet acreditado): confirmar el aviso con radiólogos de otro país, incluido TB frente
   a otras enfermedades. Regla: VinDr solo para medir, no para entrenar lo que se despliega.
2. ~~Calibración local del corte~~: hecho (2026-11-21). El médico marca TB confirmada/descartada en la revisión; con
   20 + 20 casos de la misma versión, "Desempeño del asistente" sugiere un corte (`RADIOLOGY_TB_UMBRAL_COMPATIBLE`).
3. Reintentar el ajuste del modelo de imagen cuando haya más hospitales distintos.

## 7. Reproducir (desde `backend/`)

```
.venv/Scripts/python -m scripts.evaluacion_radiologia.tb_cache          # caché con preprocesamiento de producción
.venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_entrenar --modo lineal --epocas 10 --lr 3e-3
.venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_entrenar --modo parcial --epocas 12 [--con-shenzhen]
.venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_loso
.venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_patron     # exporta patron_tb_v1.json
PYTHONIOENCODING=utf-8 .venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_ensamble
.venv-gpu/Scripts/python -m scripts.evaluacion_radiologia.tb_patron --ensamble   # exporta patron_tb_v2.json
```

`.venv-gpu`: Python 3.12, torch 2.6.0+cu124, torchvision 0.21.0+cu124, torchxrayvision 1.5.7, scikit-learn
(solo para experimentos; producción sigue en CPU sin cambios).

## 8. Citas

- Liu Y, Wu YH, Ban Y, Wang H, Cheng MM. Rethinking computer-aided tuberculosis diagnosis. CVPR 2020. (TBX11K, CC BY 4.0)
- Jaeger S, Candemir S, Antani S, et al. Two public chest X-ray datasets for computer-aided screening of pulmonary
  diseases. Quant Imaging Med Surg 2014. (Shenzhen, Montgomery)
- Chauhan A, Chauhan D, Rout C. Role of gist and PHOG features in computer-aided diagnosis of tuberculosis without
  segmentation. PLoS One 2014. (DA, DB)
- Cohen JP, et al. TorchXRayVision: A library of chest X-ray datasets and models. MIDL 2022.
