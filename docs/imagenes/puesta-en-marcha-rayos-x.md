# Puesta en marcha: asistente de IA de Rayos X (local, CPU)

Todo se ejecuta en el equipo. Las descargas ocurren **solo** al preparar, con scripts explícitos y verificación SHA-256. En funcionamiento no hay red ni código remoto.

## 1. Requisitos medidos

| Recurso | Valor |
|---|---|
| CPU | Medido en i7-10750H (6 núcleos); usa hasta 4 hilos |
| RAM libre al analizar | ≥ 2 GiB (`RADIOLOGY_VISION_MIN_FREE_MIB`); pico del trabajador ~535 MiB sin segmentación y ~930 MiB con ella |
| Disco | DenseNet 27 MB · RAG ~450 MiB · segmentación pulmonar 273 MB |
| Tiempo por estudio | ~10 s de extremo a extremo con el trabajador efímero; ~13 s con segmentación pulmonar |

## 2. Instalación (desde `backend/`, Python 3.12)

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia-cpu.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-radiologia.txt   # incluye pydicom y pylibjpeg
.\.venv\Scripts\python.exe -m pip install -r requirements-rag.txt          # evidencia documental (opcional)

.\.venv\Scripts\python.exe -m scripts.preparar_modelos_radiologia --descargar        # DenseNet XRV (obligatorio)
.\.venv\Scripts\python.exe -m scripts.preparar_rag_torax --descargar                 # corpus abierto + MiniLM (opcional)
.\.venv\Scripts\python.exe -m scripts.consultar_rag_torax --indexar
.\.venv\Scripts\python.exe -m scripts.preparar_segmentacion_pulmonar --descargar     # mapas solo en pulmones (opcional)

.\.venv\Scripts\python.exe -m alembic upgrade head    # incluye 20261115_0017 (triaje) y 20261116_0018 (lectura médica)
```

En una instalación existente, ensayar antes la migración en una copia aislada de la base (ver `AGENTS.md`).

## 3. Configuración (`backend/.env`)

```
RADIOLOGY_AI_ENABLED=true            # activa el análisis y el triaje automático al subir
RADIOLOGY_VISION_MIN_FREE_MIB=2048   # RAM libre mínima para cargar el modelo
RADIOLOGY_LUNG_MASK_ENABLED=true     # mapas solo en pulmones si se preparó la segmentación (false para ahorrar ~400 MiB y ~3 s)
# RADIOLOGY_TRIAGE_UMBRAL_ALTA=...   # solo después de calibrar con casos locales
# RADIOLOGY_TRIAGE_UMBRAL_MEDIA=...
```

Reiniciar uvicorn después de cambiar `.env`.

## 4. Verificación rápida

1. `.\.venv\Scripts\python.exe -c "import app.main"` y `pip check`.
2. `.\.venv\Scripts\python.exe -m pytest -q app/imagenes`.
3. Subir una radiografía como personal de Rayos X: en unos 10 s debe aparecer el nivel de prioridad en la bandeja.
4. Como médico, **Analizar con IA local** y revisar el índice, las 18 categorías, la comparación con el informe y la evidencia.

## 5. Problemas frecuentes

| Síntoma | Causa probable |
|---|---|
| "Memoria libre insuficiente" | Cerrar programas o bajar `RADIOLOGY_VISION_MIN_FREE_MIB` (mínimo 2048). |
| "Faltan pesos locales preparados" | No se ejecutó `preparar_modelos_radiologia --descargar`. |
| La bandeja no muestra prioridad | `RADIOLOGY_AI_ENABLED` no está en `true`, o el backend no se reinició. |
| "DICOM comprimido sin decodificador" | Falta `pylibjpeg` (`requirements-radiologia.txt`). JPEG-LS no está soportado. |
| Evidencia "no disponible" | RAG sin preparar o sin indexar (sección 2). |
| El médico no ve sus estudios | Solo aparecen estudios **publicados** de sus solicitudes. |

## 6. Datos de evaluación (no son parte del producto)

`scripts.preparar_tb_nlm --descargar` baja Shenzhen y Montgomery (NLM, ~4,4 GB) a `.datasets/tb-nlm/`. **No se deben compartir fuera del grupo ni versionar.** Sirven para repetir la evaluación con `scripts.evaluacion_radiologia.tb_externa`, `tb_sonda` y `tb_mapas`.
