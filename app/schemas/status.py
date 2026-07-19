from pydantic import BaseModel, Field

from app.core.config import Settings


def resolve_answer_model(settings: Settings) -> str:
    """Return the configured answer model for the active answer provider."""
    if settings.answer_provider == "openrouter":
        return settings.openrouter_chat_model
    if settings.answer_provider == "openai":
        return settings.openai_chat_model
    return "mock"


class PlatformStatusResponse(BaseModel):
    """Runtime platform configuration exposed to clients."""

    status: str = Field(..., description="Overall platform status.")
    embedding_provider: str = Field(..., description="Configured embedding provider.")
    answer_provider: str = Field(..., description="Configured answer provider.")
    answer_model: str = Field(..., description="Configured answer model for the active provider.")
    app_environment: str = Field(..., description="Application environment name.")


def build_platform_status(settings: Settings) -> PlatformStatusResponse:
    """Build a platform status payload from application settings."""
    return PlatformStatusResponse(
        status="ok",
        embedding_provider=settings.embedding_provider,
        answer_provider=settings.answer_provider,
        answer_model=resolve_answer_model(settings),
        app_environment=settings.app_environment,
    )
