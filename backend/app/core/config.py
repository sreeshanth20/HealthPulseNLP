"""Application settings (pydantic-settings, .env aware)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# config.py lives at backend/app/core/config.py → parents[2] == backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- application ----------------------------------------------------------
    app_name: str = "HealthPulse AI"
    app_version: str = "1.0.0"
    environment: str = "development"  # development | testing | production
    secret_key: str = "dev-secret-change-me-in-production"
    access_token_expire_minutes: int = 120
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

    # --- persistence ----------------------------------------------------------
    database_url: str = f"sqlite:///{BACKEND_DIR / 'healthpulse.db'}"
    redis_url: str | None = None

    # --- documents --------------------------------------------------------------
    document_storage_dir: str = str(BACKEND_DIR / "storage" / "documents")
    max_upload_mb: int = 20

    @field_validator("cors_origins")
    @classmethod
    def _split_origins(cls, value: str) -> list[str]:
        return [o.strip() for o in value.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
