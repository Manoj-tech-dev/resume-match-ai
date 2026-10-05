"""Centralized application configuration loaded from environment variables / `.env`."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]

LLMProviderName = Literal["auto", "mock", "openai", "gemini"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "AI Resume Analyzer"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # Stored as a raw comma-separated string so it is easy to set in `.env`.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///./data/resume_analyzer.db"

    max_upload_size_mb: float = Field(default=5, gt=0, le=50)
    max_job_description_chars: int = Field(default=20_000, ge=100)
    min_job_description_chars: int = Field(default=30, ge=1)
    max_resume_pages: int = Field(default=20, ge=1)

    llm_provider: LLMProviderName = "auto"
    llm_timeout_seconds: float = Field(default=60, gt=0)
    llm_temperature: float = Field(default=0.2, ge=0, le=2)

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-1.5-flash"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return int(self.max_upload_size_mb * 1024 * 1024)


@lru_cache
def get_settings() -> Settings:
    return Settings()
