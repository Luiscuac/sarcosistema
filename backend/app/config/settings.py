"""
Valida que existan las variables de entorno necesarias.
Equivalente a env.validation.ts
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret_key: str
    debug: bool = False
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_model_dir: str = ".models/whisper"
    whisper_cpu_threads: int = 4


settings = Settings()
