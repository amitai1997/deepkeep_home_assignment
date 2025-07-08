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
    openai_timeout: float = Field(30.0, alias="OPENAI_TIMEOUT")
    openai_retries: int = Field(3, alias="OPENAI_RETRIES")
    database_url: str = Field(
        "postgresql+asyncpg://user:pass@db/chatdb", alias="DATABASE_URL"
    )

    class Config:
        # env_file = ".env"  # removed – environment is fully controlled outside
        case_sensitive = True
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached Settings instance."""

    # Return cached settings without suppressed type errors – defaults satisfy Pydantic
    return Settings()  # pyright: ignore[reportCallIssue]
