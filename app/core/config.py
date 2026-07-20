from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

StorageBackend = Literal["local"]
EmbeddingProviderName = Literal["mock", "openai", "ollama"]
VectorStoreName = Literal["inmemory", "chroma"]
AnswerProviderName = Literal["mock", "openai", "openrouter"]


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
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_timeout_seconds: float = Field(default=30.0, ge=1)

    vector_store: VectorStoreName = "inmemory"
    vector_db_path: str = "./vector_store"
    vector_store_backend: str | None = Field(default=None, repr=False)

    answer_provider: AnswerProviderName = "mock"
    openai_chat_model: str = "gpt-4.1-mini"
    openai_temperature: float = 0.0
    openai_max_output_tokens: int = Field(default=800, ge=1)
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_chat_model: str = "openrouter/free"

    search_default_top_k: int = Field(default=5, ge=1)
    search_max_top_k: int = Field(default=50, ge=1)

    @field_validator("vector_store", mode="before")
    @classmethod
    def normalize_vector_store(cls, value: Any) -> Any:
        """Map legacy ``memory`` backend name to ``inmemory``."""
        if value == "memory":
            return "inmemory"
        return value

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_vector_store_backend(cls, data: Any) -> Any:
        """Support deprecated ``vector_store_backend`` settings field."""
        if isinstance(data, dict) and data.get("vector_store") is None:
            legacy_backend = data.get("vector_store_backend")
            if legacy_backend is not None:
                data["vector_store"] = (
                    "inmemory" if legacy_backend == "memory" else legacy_backend
                )
        return data


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def clear_settings_cache() -> None:
    """Clear cached settings for test isolation."""
    get_settings.cache_clear()
