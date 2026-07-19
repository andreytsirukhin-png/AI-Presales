import pytest

from app.core.dependencies import build_embedding_provider, clear_dependency_caches
from app.core.exceptions import EmbeddingConfigurationError
from app.infrastructure.embeddings import (
    MockEmbeddingProvider,
    OllamaEmbeddingProvider,
    OpenAIEmbeddingProvider,
)


def test_build_embedding_provider_returns_mock_by_default() -> None:
    provider = build_embedding_provider("mock", 16, "", "text-embedding-3-small")

    assert isinstance(provider, MockEmbeddingProvider)
    assert provider.dimension == 16


def test_build_embedding_provider_returns_openai_provider_with_api_key() -> None:
    clear_dependency_caches()
    provider = build_embedding_provider(
        "openai",
        1536,
        "test-key",
        "text-embedding-3-small",
    )

    assert isinstance(provider, OpenAIEmbeddingProvider)
    assert provider.dimension == 1536


def test_build_embedding_provider_requires_openai_api_key() -> None:
    with pytest.raises(EmbeddingConfigurationError):
        build_embedding_provider("openai", 1536, "", "text-embedding-3-small")


def test_build_embedding_provider_returns_ollama_provider() -> None:
    clear_dependency_caches()
    provider = build_embedding_provider(
        "ollama",
        768,
        "",
        "text-embedding-3-small",
        "http://localhost:11434",
        "nomic-embed-text",
        30.0,
    )

    assert isinstance(provider, OllamaEmbeddingProvider)
    assert provider.dimension == 768
