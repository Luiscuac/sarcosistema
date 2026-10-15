# Agente local de SarcoSistema

Componente Windows que permite a SarcoSistema inspeccionar ventanas visibles y rellenar campos editables identificados por `AutomationId` mediante UI Automation (UIA).

## Alcance de esta primera version

- Lista ventanas visibles con titulo y PID.
- Inspecciona campos editables de una ventana elegida.
- Rellena campos identificados por `AutomationId` o por nombre accesible, siempre que el selector sea unico.
- Nunca pulsa botones de guardar o publicar.
- Solo escucha en `127.0.0.1`; CORS acepta el frontend local de Vite.

Para otro origen de frontend, define `TRANSPORTADOR_ALLOWED_ORIGINS` con una lista separada por comas antes de iniciar el servicio.

La aplicacion destino debe exponer sus controles mediante Windows UI Automation y cada campo necesita un mapeo. Aplicaciones antiguas, escritorios remotos o controles dibujados como imagen pueden requerir otro metodo. Usa unicamente datos ficticios durante la prueba.

## Iniciar en Windows

Desde la carpeta `transportador` y con Python 3.11 o posterior:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

Con el agente en marcha, la documentacion interactiva esta en <http://127.0.0.1:8765/docs>.

## Probar sin el software final

Abre otra PowerShell en la raiz del repositorio y ejecuta el formulario Windows de prueba:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\transportador\demo_destino.ps1
```

Luego inicia el frontend SarcoSistema, entra a `/transcriptor` y pulsa **Conectar y detectar ventanas**. Selecciona **Programa destino de prueba**, asigna cada dato a su campo y pulsa **Rellenar campos en la aplicacion**. Verifica los valores y pulsa **Guardar fila de prueba** manualmente. El formulario es una ventana nativa real para probar UI Automation; no representa el software hospitalario final.

## Flujo previsto

1. SarcoSistema obtiene el registro de prueba.
2. El usuario elige una ventana destino desde el agente.
3. Se inspeccionan sus campos editables y se configura el mapeo de datos.
4. El agente rellena los campos; el usuario revisa y guarda manualmente.

El frontend de `/transcriptor` puede conectarse al agente local para listar ventanas, inspeccionar campos editables y rellenar el mapeo configurado. El usuario debe revisar y guardar manualmente en el software destino.


