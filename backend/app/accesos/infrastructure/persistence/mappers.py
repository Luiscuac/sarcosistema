from collections.abc import Mapping
from typing import Any

from app.accesos.domain.entities import Usuario


def mapear_usuario(row: Mapping[str, Any] | None, incluir_hash: bool = False) -> Usuario | None:
    if row is None:
        return None

    activo = (
        row["estado"] == "activo"
        and row["rol_activo"]
        and row["trabajador_estado"] == "activo"
    )
    return Usuario(
        id=row["id"],
        identificador_acceso=row["identificador_acceso"],
        rol=row["rol"],
        activo=activo,
        contrasena_hash=row["contrasena_hash"] if incluir_hash else None,
    )
