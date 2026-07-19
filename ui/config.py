"""UI configuration for the Streamlit demo."""

import os
from dataclasses import dataclass
from typing import Mapping


def _resolve_answer_model_from_env(answer_provider: str) -> str:
    """Return a local fallback answer model based on environment variables."""
    if answer_provider == "openrouter":
        return os.getenv("AI_PRESALES_OPENROUTER_CHAT_MODEL", "openrouter/free")
    if answer_provider == "openai":
        return os.getenv("AI_PRESALES_OPENAI_CHAT_MODEL", "gpt-4.1-mini")
    return "mock"


@dataclass(frozen=True)
class UiSettings:
    """Runtime settings for the Streamlit client."""

    api_base_url: str
    request_timeout_seconds: float
    embedding_provider: str
    answer_provider: str
    answer_model: str


def get_ui_settings() -> UiSettings:
    """Load base UI settings from environment variables."""
    answer_provider = os.getenv("AI_PRESALES_ANSWER_PROVIDER", "mock")
    return UiSettings(
        api_base_url=os.getenv("AI_PRESALES_API_BASE_URL", "http://localhost:8000").rstrip("/"),
        request_timeout_seconds=float(os.getenv("AI_PRESALES_UI_REQUEST_TIMEOUT", "60")),
        embedding_provider=os.getenv("AI_PRESALES_EMBEDDING_PROVIDER", "mock"),
        answer_provider=answer_provider,
        answer_model=_resolve_answer_model_from_env(answer_provider),
    )


def apply_backend_status(settings: UiSettings, status: Mapping[str, object]) -> UiSettings:
    """Merge backend provider metadata into UI settings."""
    return UiSettings(
        api_base_url=settings.api_base_url,
        request_timeout_seconds=settings.request_timeout_seconds,
        embedding_provider=str(status.get("embedding_provider", settings.embedding_provider)),
        answer_provider=str(status.get("answer_provider", settings.answer_provider)),
        answer_model=str(status.get("answer_model", settings.answer_model)),
    )
