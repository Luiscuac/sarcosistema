from app.application.ports.automatizacion_escritorio import AutomatizacionEscritorio
from app.domain.entities import ConsultaParaDemo
from app.domain.errors import ContenidoInvalido, VentanaAmbigua, VentanaNoEncontrada


CAMPOS_DEMO = {
    "peso_kg", "talla_cm", "temperatura_c", "frecuencia_cardiaca",
    "frecuencia_respiratoria", "presion_sistolica", "presion_diastolica",
    "saturacion_oxigeno", "motivo_consulta", "sintomas", "enfermedad_actual",
    "antecedentes", "examen_fisico", "hallazgos", "observaciones",
    "evaluacion_clinica", "diagnostico_principal", "diagnosticos_secundarios",
    "tratamiento", "medicamentos", "indicaciones", "estudios_solicitados",
    "referencias", "recomendaciones", "plan_seguimiento",
}
TITULO_VENTANA_DEMO = "Cuaderno de consulta externa - Demo"
PESTANA_PACIENTES = "Pacientes"
PESTANA_CONSULTA = "Nueva consulta"
BOTON_GUARDAR_CONSULTA = "Finalizar y guardar consulta"


class TransportarConsultaDemo:
    def __init__(self, escritorio: AutomatizacionEscritorio):
        self.escritorio = escritorio

    def ejecutar(self, consulta: ConsultaParaDemo):
        self._validar_consulta(consulta)
        ventanas = [
            ventana
            for ventana in self.escritorio.listar_ventanas_visibles()
            if ventana.titulo == TITULO_VENTANA_DEMO
        ]
        if not ventanas:
            raise VentanaNoEncontrada(
                f"Abre la ventana de demo «{TITULO_VENTANA_DEMO}» para transportar la consulta."
            )
        if len(ventanas) != 1:
            raise VentanaAmbigua("Hay más de una ventana del cuaderno de demo abierta.")

        handle = ventanas[0].handle
        self.escritorio.seleccionar_pestana(handle, PESTANA_PACIENTES)
        self.escritorio.seleccionar_paciente_demo(
            handle,
            [consulta.codigo_paciente, consulta.historia_clinica or ""],
            consulta.paciente_nombre,
        )
        self.escritorio.seleccionar_pestana(handle, PESTANA_CONSULTA)

        valores = {"profesional": consulta.profesional}
        valores.update({
            clave: "" if valor is None else str(valor)
            for clave, valor in consulta.datos.items()
        })
        self.escritorio.rellenar_por_automation_id(handle, valores)
        self.escritorio.activar_boton(handle, BOTON_GUARDAR_CONSULTA)
        return {
            "estado": "consulta_transportada",
            "paciente": consulta.paciente_nombre,
            "campos": len(valores),
        }

    @staticmethod
    def _validar_consulta(consulta: ConsultaParaDemo):
        claves = set(consulta.datos)
        if claves != CAMPOS_DEMO:
            raise ContenidoInvalido(
                f"Los campos de la consulta no coinciden con el perfil demo. "
                f"Faltantes: {sorted(CAMPOS_DEMO - claves)}; "
                f"desconocidos: {sorted(claves - CAMPOS_DEMO)}."
            )
        if not consulta.datos.get("motivo_consulta") or not consulta.datos.get("diagnostico_principal"):
            raise ContenidoInvalido(
                "Completa el motivo y el diagnóstico principal antes de transportar."
            )
