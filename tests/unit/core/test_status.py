import pytest

from app.core.config import Settings
from app.schemas.status import build_platform_status, resolve_answer_model


@pytest.mark.parametrize(
    ("answer_provider", "expected_model"),
    [
        ("mock", "mock"),
        ("openai", "gpt-4.1-mini"),
        ("openrouter", "openrouter/free"),
    ],
)
def test_resolve_answer_model_returns_provider_specific_model(
    answer_provider: str,
    expected_model: str,
) -> None:
    settings = Settings(answer_provider=answer_provider)

    assert resolve_answer_model(settings) == expected_model


def test_build_platform_status_includes_answer_model_for_openrouter() -> None:
    settings = Settings(
        answer_provider="openrouter",
        openrouter_chat_model="anthropic/claude-3.5-sonnet",
    )

    status = build_platform_status(settings)

    assert status.answer_provider == "openrouter"
    assert status.answer_model == "anthropic/claude-3.5-sonnet"


def test_build_platform_status_includes_answer_model_for_openai() -> None:
    settings = Settings(
        answer_provider="openai",
        openai_chat_model="gpt-4.1",
    )

    status = build_platform_status(settings)

    assert status.answer_provider == "openai"
    assert status.answer_model == "gpt-4.1"
