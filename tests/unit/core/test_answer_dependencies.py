import pytest

from app.core.dependencies import build_answer_provider, clear_dependency_caches
from app.core.exceptions import AnswerConfigurationError
from app.infrastructure.answers import (
    MockAnswerProvider,
    OpenAIAnswerProvider,
    OpenRouterAnswerProvider,
)

OPENROUTER_DEFAULTS = ("", "https://openrouter.ai/api/v1", "openrouter/free")


def test_build_answer_provider_returns_mock_by_default() -> None:
    provider = build_answer_provider("mock", "", "gpt-4.1-mini", 0.0, 800, *OPENROUTER_DEFAULTS)

    assert isinstance(provider, MockAnswerProvider)


def test_build_answer_provider_returns_openai_provider_with_api_key() -> None:
    clear_dependency_caches()
    provider = build_answer_provider(
        "openai",
        "test-key",
        "gpt-4.1-mini",
        0.0,
        800,
        *OPENROUTER_DEFAULTS,
    )

    assert isinstance(provider, OpenAIAnswerProvider)


def test_build_answer_provider_returns_openrouter_provider_with_api_key() -> None:
    clear_dependency_caches()
    provider = build_answer_provider(
        "openrouter",
        "",
        "gpt-4.1-mini",
        0.0,
        800,
        "router-key",
        "https://openrouter.ai/api/v1",
        "openrouter/free",
    )

    assert isinstance(provider, OpenRouterAnswerProvider)


def test_build_answer_provider_requires_openai_api_key() -> None:
    with pytest.raises(AnswerConfigurationError):
        build_answer_provider("openai", "", "gpt-4.1-mini", 0.0, 800, *OPENROUTER_DEFAULTS)


def test_build_answer_provider_requires_openrouter_api_key() -> None:
    with pytest.raises(AnswerConfigurationError, match="OpenRouter API key is required"):
        build_answer_provider(
            "openrouter",
            "",
            "gpt-4.1-mini",
            0.0,
            800,
            "",
            "https://openrouter.ai/api/v1",
            "openrouter/free",
        )
