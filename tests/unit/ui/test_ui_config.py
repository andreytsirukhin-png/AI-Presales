import pytest

from ui.config import UiSettings, apply_backend_status, get_ui_settings


def test_get_ui_settings_includes_answer_model() -> None:
    settings = get_ui_settings()

    assert hasattr(settings, "answer_model")
    assert settings.answer_model == "mock"


def test_get_ui_settings_resolves_openrouter_answer_model_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PRESALES_ANSWER_PROVIDER", "openrouter")
    monkeypatch.setenv("AI_PRESALES_OPENROUTER_CHAT_MODEL", "openrouter/free")

    settings = get_ui_settings()

    assert settings.answer_provider == "openrouter"
    assert settings.answer_model == "openrouter/free"


def test_get_ui_settings_resolves_openai_answer_model_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AI_PRESALES_ANSWER_PROVIDER", "openai")
    monkeypatch.setenv("AI_PRESALES_OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    settings = get_ui_settings()

    assert settings.answer_provider == "openai"
    assert settings.answer_model == "gpt-4.1-mini"


def test_apply_backend_status_overrides_provider_metadata() -> None:
    settings = UiSettings(
        api_base_url="http://localhost:8000",
        request_timeout_seconds=60.0,
        embedding_provider="mock",
        answer_provider="mock",
        answer_model="mock",
        vector_store="inmemory",
    )

    updated = apply_backend_status(
        settings,
        {
            "embedding_provider": "openai",
            "answer_provider": "openrouter",
            "answer_model": "openrouter/free",
            "vector_store": "chroma",
        },
    )

    assert updated.embedding_provider == "openai"
    assert updated.answer_provider == "openrouter"
    assert updated.answer_model == "openrouter/free"
    assert updated.vector_store == "chroma"
    assert updated.api_base_url == "http://localhost:8000"
