from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Document AI Pipeline"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    temp_dir: Path = STORAGE_DIR / "tmp"
    log_file: Path = STORAGE_DIR / "logs" / "app.log"
    max_file_size_mb: int = 20
    request_timeout_seconds: int = 90
    azure_document_intelligence_endpoint: str = Field(default="")
    azure_document_intelligence_key: str = Field(default="")
    azure_document_intelligence_classifier_id: str = Field(default="")
    frontend_api_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings instance."""
    settings = Settings()
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.log_file.parent.mkdir(parents=True, exist_ok=True)
    return settings
