import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def _settings(**overrides):
    values = {
        "database_url": "postgresql+asyncpg://app:password@db:5432/hospital",
        "jwt_secret_key": "a" * 64,
        "app_env": "production",
        "debug": False,
        "api_docs_enabled": False,
        "allowed_roles": "medico,laboratorio,enfermeria",
        "cors_allowed_origins": "",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_production_settings_accept_secure_intranet_configuration():
    settings = _settings()
    assert settings.allowed_role_codes == frozenset({"medico", "laboratorio", "enfermeria"})
    assert settings.cors_allowed_origins_list == []


@pytest.mark.parametrize("overrides, mensaje", [
    ({"jwt_secret_key": "short"}, "32 bytes"),
    ({"debug": True}, "DEBUG"),
    ({"api_docs_enabled": True}, "API_DOCS_ENABLED"),
    ({"allowed_roles": ""}, "ALLOWED_ROLES"),
    ({"cors_allowed_origins": "http://intranet"}, "HTTPS"),
    ({"cors_allowed_origins": "*"}, "HTTPS"),
])
def test_production_settings_reject_unsafe_values(overrides, mensaje):
    with pytest.raises(ValidationError, match=mensaje):
        _settings(**overrides)
