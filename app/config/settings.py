from __future__ import annotations

from functools import lru_cache
import json
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
    azure_document_intelligence_extraction_models: str = "{}"
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


def get_extraction_model_mapping(settings: Settings) -> dict[str, str]:
    """Parse extraction model mapping from environment settings."""
    raw_mapping = settings.azure_document_intelligence_extraction_models.strip() or "{}"
    try:
        parsed = json.loads(raw_mapping)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "AZURE_DOCUMENT_INTELLIGENCE_EXTRACTION_MODELS must be valid JSON."
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError(
            "AZURE_DOCUMENT_INTELLIGENCE_EXTRACTION_MODELS must be a JSON object."
        )

    return {
        str(document_type).strip(): str(model_id).strip()
        for document_type, model_id in parsed.items()
        if str(document_type).strip() and str(model_id).strip()
    }
