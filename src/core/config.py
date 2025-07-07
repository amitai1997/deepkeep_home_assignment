"""Application configuration module."""

from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """App settings loaded from environment variables."""

    openai_api_key: str = Field("", alias="OPENAI_API_KEY")
    block_minutes: int = Field(60 * 24, alias="BLOCK_MINUTES")
    use_mock_openai: bool = Field(False, alias="USE_MOCK_OPENAI")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""

    return Settings()  # type: ignore[arg-type, call-arg]
    # mypy/pyright sometimes assume required fields even when defaults exist.
