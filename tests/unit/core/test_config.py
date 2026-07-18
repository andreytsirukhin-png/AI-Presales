from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings, clear_settings_cache, get_settings


@pytest.fixture(autouse=True)
def reset_settings_cache() -> None:
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_settings_default_values() -> None:
    settings = Settings()

    assert settings.app_name == "AI Presales"
    assert settings.app_environment == "development"
    assert settings.debug is False
    assert settings.storage_backend == "local"
    assert settings.storage_path == "uploads"
    assert settings.embedding_provider == "mock"
    assert settings.embedding_dimension == 16
    assert settings.openai_api_key == ""
    assert settings.openai_embedding_model == "text-embedding-3-small"
    assert settings.vector_store_backend == "memory"
    assert settings.answer_provider == "mock"
    assert settings.search_default_top_k == 5
    assert settings.search_max_top_k == 50


def test_settings_loads_environment_variable_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PRESALES_APP_NAME", "Test Presales")
    monkeypatch.setenv("AI_PRESALES_APP_ENVIRONMENT", "testing")
    monkeypatch.setenv("AI_PRESALES_STORAGE_PATH", "./tmp/test-data")
    monkeypatch.setenv("AI_PRESALES_EMBEDDING_DIMENSION", "32")

    settings = Settings()

    assert settings.app_name == "Test Presales"
    assert settings.app_environment == "testing"
    assert settings.storage_path == "./tmp/test-data"
    assert settings.embedding_dimension == 32


def test_settings_parses_boolean_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PRESALES_DEBUG", "true")

    settings = Settings()

    assert settings.debug is True


def test_settings_parses_integer_environment_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PRESALES_SEARCH_DEFAULT_TOP_K", "7")
    monkeypatch.setenv("AI_PRESALES_SEARCH_MAX_TOP_K", "25")

    settings = Settings()

    assert settings.search_default_top_k == 7
    assert settings.search_max_top_k == 25


@pytest.mark.parametrize(
    "env_name",
    [
        "AI_PRESALES_STORAGE_BACKEND",
        "AI_PRESALES_EMBEDDING_PROVIDER",
        "AI_PRESALES_VECTOR_STORE_BACKEND",
        "AI_PRESALES_ANSWER_PROVIDER",
    ],
)
def test_settings_rejects_invalid_backend_or_provider(
    monkeypatch: pytest.MonkeyPatch,
    env_name: str,
) -> None:
    monkeypatch.setenv(env_name, "unsupported")

    with pytest.raises(ValidationError):
        Settings()


def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()

    assert first is second


def test_settings_loads_from_dotenv_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "AI_PRESALES_APP_NAME=Dotenv Presales",
                "AI_PRESALES_DEBUG=true",
                "AI_PRESALES_EMBEDDING_DIMENSION=24",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AI_PRESALES_APP_NAME", raising=False)
    monkeypatch.delenv("AI_PRESALES_DEBUG", raising=False)
    monkeypatch.delenv("AI_PRESALES_EMBEDDING_DIMENSION", raising=False)

    settings = Settings()

    assert settings.app_name == "Dotenv Presales"
    assert settings.debug is True
    assert settings.embedding_dimension == 24
