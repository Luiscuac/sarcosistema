"""
Valida que existan las variables de entorno necesarias.
Equivalente a env.validation.ts
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str
    jwt_secret_key: str
    debug: bool = False
    cors_allowed_origins: str = "http://localhost:5173"
    allowed_roles: str = ""
    api_docs_enabled: bool = True
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_model_dir: str = ".models/whisper"
    whisper_cpu_threads: int = 4
    whisper_beam_size: int = Field(default=5, ge=1, le=10)
    clinical_extractor_enabled: bool = False
    ollama_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5:3b'
    clinical_extractor_timeout_seconds: int = 180
    radiology_ai_enabled: bool = False
    radiology_storage_dir: str = '.storage/radiologia'
    radiology_vision_min_free_mib: int = Field(default=4096,ge=2048)
    radiology_score_threshold: float = Field(default=0.5,ge=0,le=1)

    # Examenes complementarios de imagen: solo imagen hoy, abierto a video/audio.
    imagenes_tipos_permitidos: str = (
        'image/jpeg,image/png,image/webp,image/gif,image/tiff,application/pdf,application/dicom'
    )
    imagenes_max_mb: int = 15
    imagenes_dicom_max_mb: int = 100
    imagenes_max_archivos: int = 10
    imagenes_storage_dir: str = 'storage/imagenes'

    @model_validator(mode="after")
    def validar_produccion(self):
        if self.app_env != "production":
            return self
        if self.debug:
            raise ValueError("DEBUG debe estar desactivado en producción.")
        if len(self.jwt_secret_key.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY debe tener al menos 32 bytes en producción.")
        if self.jwt_secret_key == "cambiar-este-valor-en-produccion":
            raise ValueError("JWT_SECRET_KEY conserva el valor de ejemplo.")
        if self.api_docs_enabled:
            raise ValueError("API_DOCS_ENABLED debe estar desactivado en producción.")
        if self.allowed_role_codes is None:
            raise ValueError("ALLOWED_ROLES debe limitar los roles en producción.")
        if any(
            origin == "*" or not origin.startswith("https://")
            for origin in self.cors_allowed_origins_list
        ):
            raise ValueError("CORS_ALLOWED_ORIGINS debe contener solo orígenes HTTPS explícitos.")
        return self

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def allowed_role_codes(self) -> frozenset[str] | None:
        roles = frozenset(
            role.strip()
            for role in self.allowed_roles.split(",")
            if role.strip()
        )
        return roles or None

    @property
    def imagenes_tipos_lista(self) -> tuple[str, ...]:
        return tuple(t.strip() for t in self.imagenes_tipos_permitidos.split(',') if t.strip())


settings = Settings()
