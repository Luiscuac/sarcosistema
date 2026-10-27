from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pywinauto import Desktop

FRONTEND_ORIGINS = {
    origin.strip()
    for origin in os.getenv(
        "TRANSPORTADOR_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
}

app = FastAPI(
    title="Agente local SarcoSistema",
    version="0.1.0",
    description="Puente local para descubrir ventanas y rellenar controles de Windows configurados.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(FRONTEND_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class CampoRelleno(BaseModel):
    selector_tipo: Literal["automation_id", "nombre", "indice"]
    selector: str = Field(min_length=1, max_length=256)
    valor: str = Field(max_length=10000)


class SolicitudRelleno(BaseModel):
    campos: list[CampoRelleno] = Field(min_length=1, max_length=100)


@app.middleware("http")
async def rechazar_origenes_web_desconocidos(request, call_next):
    origin = request.headers.get("origin")
    if origin and origin not in FRONTEND_ORIGINS:
        return JSONResponse(status_code=403, content={"detail": "Origen web no permitido."})
    return await call_next(request)


def _ventanas_visibles() -> list[Any]:
    try:
        return Desktop(backend="uia").windows(visible_only=True, top_level_only=True)
    except Exception as error:
        raise HTTPException(status_code=503, detail="No se pudieron inspeccionar las ventanas de Windows.") from error


def _ventana(handle: int):
    try:
        ventana = Desktop(backend="uia").window(handle=handle)
        if not ventana.exists(timeout=1) or not ventana.is_visible():
            raise HTTPException(status_code=404, detail="La ventana no existe o no esta visible.")
        return ventana
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=404, detail="No se pudo encontrar esa ventana.") from error


@app.get("/health")
def health():
    return {"estado": "disponible", "agente": "SarcoSistema Windows UIA"}


@app.get("/v1/ventanas")
def listar_ventanas():
    resultado = []
    for ventana in _ventanas_visibles():
        try:
            titulo = ventana.window_text().strip()
            if titulo:
                resultado.append({"handle": ventana.handle, "titulo": titulo[:500], "proceso_id": ventana.process_id()})
        except Exception:
            continue
    return resultado


@app.get("/v1/ventanas/{handle}/campos")
def listar_campos_editables(handle: int):
    ventana = _ventana(handle)
    try:
        elementos = ventana.descendants(control_type="Edit")
    except Exception as error:
        raise HTTPException(status_code=422, detail="La ventana no permite inspeccionar sus campos.") from error

    controles = []
    for indice, elemento in enumerate(elementos):
        try:
            info = elemento.element_info
            automation_id = info.automation_id or ""
            nombre = (info.name or elemento.window_text() or "").strip()[:300]
            selector_tipo = "automation_id" if automation_id else "nombre"
            selector = automation_id or nombre
            controles.append(
                {
                    "automation_id": automation_id,
                    "nombre": nombre,
                    "tipo": info.control_type,
                    "habilitado": elemento.is_enabled(),
                    "selector_tipo": selector_tipo,
                    "selector": selector,
                    "indice": indice,
                    "configurable": bool(selector),
                }
            )
        except Exception:
            continue
    return controles


@app.post("/v1/ventanas/{handle}/rellenar")
def rellenar_campos(handle: int, solicitud: SolicitudRelleno):
    ventana = _ventana(handle)
    try:
        controles = ventana.descendants(control_type="Edit")
    except Exception as error:
        raise HTTPException(status_code=422, detail="La ventana no permite acceder a sus campos.") from error

    por_selector: dict[tuple[str, str], list[Any]] = {}
    for indice, control in enumerate(controles):
        por_selector.setdefault(("indice", str(indice)), []).append(control)
        info = control.element_info
        automation_id = info.automation_id or ""
        nombre = (info.name or control.window_text() or "").strip()
        if automation_id:
            por_selector.setdefault(("automation_id", automation_id), []).append(control)
        if nombre:
            por_selector.setdefault(("nombre", nombre), []).append(control)

    resueltos = []
    for campo in solicitud.campos:
        encontrados = por_selector.get((campo.selector_tipo, campo.selector), [])
        if not encontrados:
            raise HTTPException(status_code=422, detail="No se encontro un campo editable con ese selector.")
        if len(encontrados) > 1:
            raise HTTPException(status_code=409, detail="El selector no identifica un campo unico.")
        control = encontrados[0]
        if not control.is_enabled():
            raise HTTPException(status_code=409, detail="El campo seleccionado esta deshabilitado.")
        resueltos.append((campo, control))

    completados = []
    for campo, control in resueltos:
        try:
            control.set_edit_text(campo.valor)
        except Exception as error:
            raise HTTPException(status_code=422, detail="Windows no permitio escribir en un campo seleccionado.") from error
        completados.append(campo.selector)

    return {
        "estado": "campos_rellenados",
        "campos": completados,
        "guardar_automaticamente": False,
        "mensaje": "Revisa los valores en la aplicacion destino antes de guardarlos.",
    }
