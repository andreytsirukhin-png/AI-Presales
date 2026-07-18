from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_embedding_provider
from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


class OverrideEmbeddingProvider(MockEmbeddingProvider):
    """Test double that records embedding calls."""

    def __init__(self) -> None:
        super().__init__(dimension=16)
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return super().embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.extend(texts)
        return super().embed_texts(texts)


def test_dependency_override_can_replace_embedding_provider() -> None:
    override_provider = OverrideEmbeddingProvider()
    app.dependency_overrides[get_embedding_provider] = lambda: override_provider
    try:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "rfp.pdf",
                    BytesIO(make_text_pdf("OpenAI override integration test")),
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        index_response = client.post(f"/api/v1/documents/{document_id}/index")
        assert index_response.status_code == 200
        assert override_provider.calls

        search_response = client.post(
            f"/api/v1/documents/{document_id}/search",
            json={"query": "OpenAI override integration test", "top_k": 5},
        )
        assert search_response.status_code == 200
    finally:
        app.dependency_overrides.clear()


def test_openai_provider_build_requires_api_key_via_dependency_override() -> None:
    from app.core.config import Settings, get_settings
    from app.core.dependencies import build_embedding_provider, clear_dependency_caches

    override_settings = Settings(
        embedding_provider="openai",
        embedding_dimension=1536,
        openai_api_key="",
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        with pytest.raises(Exception) as exc_info:
            build_embedding_provider(
                override_settings.embedding_provider,
                override_settings.embedding_dimension,
                override_settings.openai_api_key,
                override_settings.openai_embedding_model,
            )
        assert "OpenAI API key is required" in str(exc_info.value)
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()
