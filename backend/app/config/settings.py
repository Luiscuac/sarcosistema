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
    clinical_extractor_enabled: bool = False
    ollama_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen2.5:3b'
    clinical_extractor_timeout_seconds: int = 180

    # Examenes complementarios de imagen: solo imagen hoy, abierto a video/audio.
    imagenes_tipos_permitidos: str = (
        'image/jpeg,image/png,image/webp,image/gif,image/tiff,application/pdf,application/dicom'
    )
    imagenes_max_mb: int = 15
    imagenes_dicom_max_mb: int = 100
    imagenes_max_archivos: int = 10
    imagenes_storage_dir: str = 'storage/imagenes'

    @property
    def imagenes_tipos_lista(self) -> tuple[str, ...]:
        return tuple(t.strip() for t in self.imagenes_tipos_permitidos.split(',') if t.strip())


settings = Settings()
