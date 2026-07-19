from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.dependencies import clear_dependency_caches
from app.main import app

client = TestClient(app)


def test_platform_status_endpoint_returns_provider_metadata() -> None:
    override_settings = Settings(
        embedding_provider="mock",
        answer_provider="mock",
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["embedding_provider"] == "mock"
        assert payload["answer_provider"] == "mock"
        assert payload["answer_model"] == "mock"
        assert set(payload.keys()) == {
            "status",
            "embedding_provider",
            "answer_provider",
            "answer_model",
            "app_environment",
        }
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()


def test_platform_status_endpoint_returns_openrouter_model() -> None:
    override_settings = Settings(
        answer_provider="openrouter",
        openrouter_chat_model="openrouter/free",
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        payload = response.json()
        assert payload["answer_provider"] == "openrouter"
        assert payload["answer_model"] == "openrouter/free"
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()


def test_platform_status_endpoint_returns_openai_model() -> None:
    override_settings = Settings(
        answer_provider="openai",
        openai_chat_model="gpt-4.1",
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        response = client.get("/api/v1/status")

        assert response.status_code == 200
        payload = response.json()
        assert payload["answer_provider"] == "openai"
        assert payload["answer_model"] == "gpt-4.1"
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()
