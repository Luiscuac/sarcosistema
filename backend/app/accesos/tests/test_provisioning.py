from collections import deque

import pytest

from app.accesos.infrastructure.provisioning import crear_cuenta


class Resultado:
    def __init__(self, valor):
        self.valor = valor

    def scalar_one_or_none(self):
        return self.valor

    def scalar_one(self):
        return self.valor


class SesionEspia:
    def __init__(self, resultados):
        self.resultados = deque(resultados)
        self.consultas = []

    async def execute(self, consulta, parametros=None):
        self.consultas.append((str(consulta), parametros))
        valor = self.resultados.popleft() if self.resultados else None
        return Resultado(valor)


@pytest.mark.asyncio
async def test_provisionamiento_solo_crea_roles_autorizados():
    db = SesionEspia([])
    with pytest.raises(ValueError, match="rol no está habilitado"):
        await crear_cuenta(db, "cuenta", 7, "farmacia", "hash")
    assert db.consultas == []


@pytest.mark.asyncio
async def test_provisionamiento_no_modifica_una_cuenta_existente():
    db = SesionEspia([22])
    with pytest.raises(ValueError, match="ya existe"):
        await crear_cuenta(db, "cuenta", 7, "laboratorio", "hash")
    assert len(db.consultas) == 1


@pytest.mark.asyncio
async def test_medico_debe_tener_registro_profesional_activo():
    db = SesionEspia([None, 7, None])
    with pytest.raises(ValueError, match="registro médico activo"):
        await crear_cuenta(db, "medico", 7, "medico", "hash")
    assert len(db.consultas) == 3


@pytest.mark.asyncio
async def test_provisionamiento_crea_solo_para_trabajador_activo():
    db = SesionEspia([None, 7, 3, 18])
    usuario_id = await crear_cuenta(db, " enfermeria ", 7, "enfermeria", "hash")
    assert usuario_id == 18
    consulta, parametros = db.consultas[-1]
    assert "INSERT INTO public.usuario" in consulta
    assert parametros == {
        "identificador": "enfermeria",
        "hash": "hash",
        "rol_id": 3,
        "trabajador_id": 7,
    }
