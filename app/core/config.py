from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

StorageBackend = Literal["local"]
EmbeddingProviderName = Literal["mock", "openai"]
VectorStoreBackend = Literal["memory"]
AnswerProviderName = Literal["mock"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="AI_PRESALES_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Presales"
    app_environment: str = "development"
    debug: bool = False

    storage_backend: StorageBackend = "local"
    storage_path: str = "uploads"

    embedding_provider: EmbeddingProviderName = "mock"
    embedding_dimension: int = Field(default=16, ge=1)
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    vector_store_backend: VectorStoreBackend = "memory"

    answer_provider: AnswerProviderName = "mock"

    search_default_top_k: int = Field(default=5, ge=1)
    search_max_top_k: int = Field(default=50, ge=1)


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings for test isolation."""
    get_settings.cache_clear()
