from app.ia.transcriptor.domain.entities import RegistroPrueba


class RepositorioRegistrosPrueba:
    """Datos ficticios para ensayar la automatización sin consultar la BD clínica."""

    _registros = (
        RegistroPrueba("demo-001", "PA-TEST-001", "Paciente de prueba Uno", "2026-01-15", "Hemoglobina", "13.8", "g/dL"),
        RegistroPrueba("demo-002", "PA-TEST-002", "Paciente de prueba Dos", "2026-01-16", "Glucosa", "92", "mg/dL"),
        RegistroPrueba("demo-003", "PA-TEST-003", "Paciente de prueba Tres", "2026-01-17", "Creatinina", "0.9", "mg/dL"),
    )

    def listar(self) -> list[RegistroPrueba]:
        return list(self._registros)

    def obtener(self, identificador: str) -> RegistroPrueba | None:
        return next((registro for registro in self._registros if registro.id == identificador), None)
