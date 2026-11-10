# Agente local de SarcoSistema

Puente Windows UI Automation usado desde el formulario de consulta médica. En esta primera integración automatiza únicamente el cuaderno local de demostración, con datos ficticios. No automatiza el sistema hospitalario oficial.

## Estructura

- `app/domain/`: entidades y errores del dominio.
- `app/application/`: puertos y casos de uso.
- `app/infrastructure/ui_automation/`: adaptador de Windows UI Automation con pywinauto.
- `app/presentation/`: rutas HTTP, esquemas, dependencias y traducción de errores.
- `app/container.py` y `app/main.py`: composición de dependencias y configuración de FastAPI.

## Iniciar el agente

Desde la carpeta `transportador`, con Python 3.11 o posterior:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765
```

El agente escucha solo en `127.0.0.1`. Su estado está disponible en <http://127.0.0.1:8765/health>.

## Probar el transporte de una consulta

Abre otra PowerShell desde la raíz del repositorio e inicia el destino de demostración:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\transportador\cuaderno_interacciones.ps1
```

Inicia SarcoSistema con la cuenta `medico_demo`, abre una consulta para el paciente de prueba `PAC-DEMO-CONSULTA-001` y completa motivo, diagnóstico y los demás campos deseados. Con el agente y el cuaderno demo abiertos, pulsa **Transportar a demo destino** una sola vez.

El agente localiza la ventana del cuaderno por su título, escribe el código o la historia clínica en la búsqueda del cuaderno y selecciona la coincidencia única (con el nombre como respaldo). Después abre la pestaña de consulta, rellena los campos por sus `AutomationId` y activa **Finalizar y guardar consulta**. El paciente debe existir en el destino y tener un identificador compartido con SarcoSistema; el agente no crea pacientes. La consulta aparece en el historial: selecciónala y pulsa **Ver consulta seleccionada** o haz doble clic para revisar todos sus datos. Los datos se guardan solo en memoria y se pierden al cerrar la ventana.

## Alcance actual

- El transporte usa los valores actuales del formulario, incluso antes de guardarlo en SarcoSistema.
- El agente valida que estén presentes los campos requeridos y que cada control destino tenga un identificador UIA único.
- La automatización está acoplada al título, las pestañas, el control de pacientes y los identificadores definidos por `cuaderno_interacciones.ps1`.
- Para integrar otro destino habrá que inspeccionar su árbol UIA y crear un perfil de controles específico.
- Usa solo datos ficticios durante las pruebas.
