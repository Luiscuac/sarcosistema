import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_credenciales_invalidas(client: AsyncClient):
    response = await client.post(
        "/accesos/login", 
        json={"identificador_acceso": "no_existe", "contrasena": "invalida"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas."

@pytest.mark.asyncio
async def test_acceso_endpoint_protegido_sin_token(client: AsyncClient):
    response = await client.get("/accesos/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
