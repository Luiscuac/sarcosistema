import unicodedata
from typing import Any

from pywinauto import Desktop

from app.domain.entities import CampoDestino, CampoEditable, VentanaVisible
from app.domain.errors import (
    ControlDeshabilitado,
    ControlNoEncontrado,
    FalloUIA,
    SelectorAmbiguo,
    VentanaNoEncontrada,
)


class PywinautoEscritorio:
    """Adaptador de infraestructura para Windows UI Automation."""

    def listar_ventanas_visibles(self) -> list[VentanaVisible]:
        try:
            ventanas = Desktop(backend="uia").windows(
                visible_only=True, top_level_only=True
            )
        except Exception as error:
            raise FalloUIA("No se pudieron inspeccionar las ventanas de Windows.") from error

        resultado = []
        for ventana in ventanas:
            try:
                titulo = ventana.window_text().strip()
                if titulo:
                    try:
                        proceso_id = ventana.process_id()
                    except Exception:
                        proceso_id = 0
                    resultado.append(
                        VentanaVisible(ventana.handle, titulo[:500], proceso_id)
                    )
            except Exception:
                continue
        return resultado

    def obtener_ventana_visible(self, handle: int) -> VentanaVisible:
        ventana = self._ventana(handle)
        try:
            titulo = ventana.window_text().strip()
            proceso_id = ventana.process_id()
            return VentanaVisible(handle, titulo[:500], proceso_id)
        except Exception as error:
            raise FalloUIA("No se pudo leer la ventana seleccionada.") from error

    def listar_campos_editables(self, handle: int) -> list[CampoEditable]:
        ventana = self._ventana(handle)
        try:
            elementos = ventana.descendants(control_type="Edit")
        except Exception as error:
            raise FalloUIA("La ventana no permite inspeccionar sus campos editables.") from error

        controles = []
        for indice, elemento in enumerate(elementos):
            try:
                info = elemento.element_info
                automation_id = info.automation_id or ""
                nombre = (info.name or elemento.window_text() or "").strip()[:300]
                selector_tipo = "automation_id" if automation_id else "nombre"
                selector = automation_id or nombre
                controles.append(
                    CampoEditable(
                        automation_id=automation_id,
                        nombre=nombre,
                        tipo=info.control_type,
                        habilitado=elemento.is_enabled(),
                        selector_tipo=selector_tipo,
                        selector=selector,
                        indice=indice,
                        configurable=bool(selector),
                    )
                )
            except Exception:
                continue
        return controles

    def rellenar_campos(self, handle: int, campos: list[CampoDestino]) -> list[str]:
        ventana = self._ventana(handle)
        try:
            controles = ventana.descendants(control_type="Edit")
        except Exception as error:
            raise FalloUIA("La ventana no permite acceder a sus campos editables.") from error

        por_selector: dict[tuple[str, str], list[Any]] = {}
        for indice, control in enumerate(controles):
            por_selector.setdefault(("indice", str(indice)), []).append(control)
            try:
                info = control.element_info
                automation_id = info.automation_id or ""
                nombre = (info.name or control.window_text() or "").strip()
            except Exception:
                continue
            if automation_id:
                por_selector.setdefault(("automation_id", automation_id), []).append(control)
            if nombre:
                por_selector.setdefault(("nombre", nombre), []).append(control)

        resueltos = []
        for campo in campos:
            encontrados = por_selector.get((campo.selector_tipo, campo.selector), [])
            if not encontrados:
                raise ControlNoEncontrado("No se encontró un campo editable con ese selector.")
            if len(encontrados) > 1:
                raise SelectorAmbiguo("El selector no identifica un campo único.")
            control = encontrados[0]
            if not control.is_enabled():
                raise ControlDeshabilitado("El campo seleccionado está deshabilitado.")
            resueltos.append((campo, control))

        completados = []
        for campo, control in resueltos:
            try:
                control.set_edit_text(campo.valor)
            except Exception as error:
                raise FalloUIA("Windows no permitió escribir en un campo seleccionado.") from error
            completados.append(campo.selector)
        return completados

    def seleccionar_pestana(self, handle: int, nombre: str) -> None:
        ventana = self._ventana(handle)
        pestañas = self._controles_por_nombre(ventana, "TabItem", nombre)
        if not pestañas:
            raise ControlNoEncontrado(f"No se encontró la pestaña «{nombre}».")
        if len(pestañas) != 1:
            raise SelectorAmbiguo(f"El nombre «{nombre}» coincide con varias pestañas.")
        try:
            pestañas[0].select()
        except Exception as error:
            raise FalloUIA(f"Windows no permitió abrir la pestaña «{nombre}».") from error

    def seleccionar_paciente_demo(
        self, handle: int, identificadores: list[str], nombre: str
    ) -> None:
        ventana = self._ventana(handle)
        # El cuaderno demo filtra su ListBox al escribir en este campo.
        # La búsqueda usa identificadores compartidos primero y nombre al final.
        campos_busqueda = [
            control for control in self._controles(ventana, "Edit")
            if (
                (getattr(control.element_info, "automation_id", "") or "") == "buscarPaciente"
                or "buscar paciente" in self._normalizar(
                    getattr(control.element_info, "name", "") or ""
                )
            )
        ]
        terminos = [valor.strip() for valor in identificadores if valor and valor.strip()]
        if nombre.strip():
            terminos.append(nombre.strip())
        candidatos = []
        if len(campos_busqueda) == 1:
            for termino in terminos:
                try:
                    campos_busqueda[0].set_edit_text(termino)
                except Exception as error:
                    raise FalloUIA("No se pudo buscar al paciente en el cuaderno demo.") from error
                elementos = self._controles(ventana, "ListItem")
                token = self._normalizar(termino)
                candidatos = [
                    elemento for elemento in elementos
                    if token and token in self._normalizar(self._nombre(elemento))
                ]
                if candidatos:
                    break
        else:
            elementos = self._controles(ventana, "ListItem")
            tokens = [self._normalizar(valor) for valor in terminos]
            candidatos = [
                elemento for elemento in elementos
                if any(token and token in self._normalizar(self._nombre(elemento)) for token in tokens)
            ]
        if not candidatos:
            raise ControlNoEncontrado(
                "El paciente de SarcoSistema no aparece en la lista del cuaderno demo."
            )
        if len(candidatos) != 1:
            raise SelectorAmbiguo(
                "El identificador del paciente coincide con varias filas de la demo destino."
            )
        try:
            candidatos[0].select()
        except Exception as error:
            raise FalloUIA("Windows no permitió seleccionar al paciente en la demo.") from error

    def rellenar_por_automation_id(self, handle: int, valores: dict[str, str]) -> None:
        ventana = self._ventana(handle)
        controles = self._controles(ventana, "Edit")
        por_id: dict[str, list[Any]] = {}
        for control in controles:
            try:
                automation_id = control.element_info.automation_id or ""
            except Exception:
                continue
            if automation_id:
                por_id.setdefault(automation_id, []).append(control)

        resueltos = []
        for automation_id, valor in valores.items():
            encontrados = por_id.get(automation_id, [])
            if not encontrados:
                raise ControlNoEncontrado(
                    f"El campo «{automation_id}» no existe en el cuaderno demo."
                )
            if len(encontrados) != 1:
                raise SelectorAmbiguo(
                    f"El campo «{automation_id}» no tiene un identificador UIA único."
                )
            control = encontrados[0]
            if not control.is_enabled():
                raise ControlDeshabilitado(f"El campo «{automation_id}» está deshabilitado.")
            resueltos.append((automation_id, valor, control))

        for automation_id, valor, control in resueltos:
            try:
                control.set_edit_text(valor)
            except Exception as error:
                raise FalloUIA(
                    f"Windows no permitió rellenar el campo «{automation_id}»."
                ) from error

    def activar_boton(self, handle: int, nombre: str) -> None:
        ventana = self._ventana(handle)
        botones = self._controles_por_nombre(ventana, "Button", nombre)
        if not botones:
            raise ControlNoEncontrado(f"No se encontró el botón «{nombre}».")
        if len(botones) != 1:
            raise SelectorAmbiguo(f"El nombre «{nombre}» coincide con varios botones.")
        if not botones[0].is_enabled():
            raise ControlDeshabilitado(f"El botón «{nombre}» está deshabilitado.")
        try:
            botones[0].invoke()
        except Exception as error:
            raise FalloUIA(f"Windows no permitió activar el botón «{nombre}».") from error

    def _ventana(self, handle: int):
        try:
            ventana = Desktop(backend="uia").window(handle=handle)
            if not ventana.exists(timeout=1) or not ventana.is_visible():
                raise VentanaNoEncontrada("La ventana no existe o no está visible.")
            return ventana
        except VentanaNoEncontrada:
            raise
        except Exception as error:
            raise VentanaNoEncontrada("No se pudo encontrar esa ventana.") from error

    @staticmethod
    def _controles(ventana, tipo: str):
        try:
            return ventana.descendants(control_type=tipo)
        except Exception as error:
            raise FalloUIA(f"No se pudieron inspeccionar los controles {tipo} de la ventana.") from error

    def _controles_por_nombre(self, ventana, tipo: str, nombre: str):
        encontrados = []
        for control in self._controles(ventana, tipo):
            if self._nombre(control).strip() == nombre:
                encontrados.append(control)
        return encontrados

    @staticmethod
    def _nombre(control) -> str:
        try:
            return (control.element_info.name or control.window_text() or "").strip()
        except Exception:
            return ""

    @staticmethod
    def _normalizar(texto: str) -> str:
        descompuesto = unicodedata.normalize("NFD", texto.casefold())
        return "".join(
            caracter
            for caracter in descompuesto
            if unicodedata.category(caracter) != "Mn"
        )
