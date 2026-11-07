"""Ejemplo ilustrativo para inspeccionar controles UI Automation.

El árbol y los automation_id de abajo son inventados. Cada software decide
qué controles expone y qué identificadores les asigna.

Uso en Windows:
    python -m examples.inspeccionar_arbol_uia "Nombre de la ventana"
"""

import sys

from pywinauto import Desktop


ARBOL_HIPOTETICO = """
Window - 'Historia Clínica' (L0, …)
   | TabControl - 'mainTabs' (L1)
   |    | TabItem - 'Pacientes' (L2, automation_id='patientsTab')
   |    | TabItem - 'Atención' (L2, automation_id='encounterTab')
   | Edit - 'Buscar paciente' (L1, automation_id='patientSearchInput')
   | DataGrid - 'Resultados' (L1, automation_id='patientsGrid')
   | Edit - 'Motivo de consulta' (L1, automation_id='reasonInput')
   | Edit - 'Diagnóstico' (L1, automation_id='diagnosisInput')
   | Button - 'Guardar' (L1, automation_id='saveEncounterButton')
""".strip()


def inspeccionar_ventana(titulo: str) -> None:
    """Imprime el árbol UIA y los selectores disponibles en una ventana."""
    ventana = Desktop(backend="uia").window(title=titulo)
    ventana.wait("exists visible", timeout=5)

    print("Árbol de controles según pywinauto:")
    ventana.print_control_identifiers()
    print("\nDatos útiles para crear selectores:")
    inspeccionar_selectores(ventana)


def inspeccionar_selectores(ventana) -> None:
    """Recorre controles y muestra sus atributos más útiles para automatizar."""
    for indice, control in enumerate(ventana.descendants()):
        try:
            info = control.element_info
            nombre = (info.name or "").replace("\n", " ").strip()
            automation_id = info.automation_id or "(sin automation_id)"
            tipo = info.control_type or "(tipo no expuesto)"
            habilitado = control.is_enabled()
            print(
                f"[{indice}] tipo={tipo!r} nombre={nombre!r} "
                f"automation_id={automation_id!r} habilitado={habilitado}"
            )
        except Exception as error:
            print(f"[{indice}] No se pudieron leer los datos del control: {error}")


def ejemplo_selectores_por_id(handle: int) -> None:
    """Ejemplos de selectores si la aplicación expone esos automation_id."""
    ventana = Desktop(backend="uia").window(handle=handle)

    motivo = ventana.child_window(
        auto_id="reasonInput", control_type="Edit"
    )
    guardar = ventana.child_window(
        auto_id="saveEncounterButton", control_type="Button"
    )

    # Acciones ilustrativas: validar los controles antes de escribir o guardar.
    if motivo.exists() and motivo.is_enabled():
        motivo.set_edit_text("Dolor abdominal desde hace tres días")
    if guardar.exists() and guardar.is_enabled():
        guardar.invoke()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Árbol hipotético de ejemplo:\n")
        print(ARBOL_HIPOTETICO)
        print("\nPara inspeccionar una ventana real, pasa su título entre comillas.")
        raise SystemExit(0)

    inspeccionar_ventana(sys.argv[1])
