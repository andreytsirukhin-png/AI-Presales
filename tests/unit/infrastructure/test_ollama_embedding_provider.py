from types import SimpleNamespace

import httpx
import pytest

from app.core.exceptions import EmbeddingProviderError, InvalidEmbeddingDimensionError
from app.infrastructure.embeddings.ollama_provider import (
    DEFAULT_OLLAMA_BASE_URL,
    OLLAMA_EMBED_PATH,
    OllamaEmbeddingProvider,
)


class FakeOllamaClient:
    """Test double for an Ollama HTTP client."""

    def __init__(
        self,
        *,
        vectors: list[list[float]] | None = None,
        error: Exception | None = None,
        status_code: int = 200,
    ) -> None:
        self.vectors = vectors or [[0.1, 0.2, 0.3]]
        self.error = error
        self.status_code = status_code
        self.calls: list[dict[str, object]] = []

    def post(self, url: str, *, json: dict[str, object]) -> SimpleNamespace:
        self.calls.append({"url": url, "json": json})
        if self.error is not None:
            raise self.error

        input_value = json["input"]
        if isinstance(input_value, str):
            count = 1
        else:
            count = len(input_value)

        if len(self.vectors) == 1 and count > 1:
            response_vectors = [self.vectors[0] for _ in range(count)]
        else:
            response_vectors = self.vectors

        return SimpleNamespace(
            status_code=self.status_code,
            json=lambda: {"embeddings": response_vectors},
        )


@pytest.fixture
def provider() -> OllamaEmbeddingProvider:
    client = FakeOllamaClient(vectors=[[0.1, 0.2, 0.3]])
    return OllamaEmbeddingProvider(
        base_url=DEFAULT_OLLAMA_BASE_URL,
        model="nomic-embed-text",
        dimension=3,
        client=client,
    )


def test_embed_returns_vector_for_single_text(provider: OllamaEmbeddingProvider) -> None:
    vector = provider.embed("hello world")

    assert vector == [0.1, 0.2, 0.3]


def test_embed_posts_to_ollama_embed_endpoint(provider: OllamaEmbeddingProvider) -> None:
    client = provider._client
    assert isinstance(client, FakeOllamaClient)

    provider.embed("hello world")

    assert len(client.calls) == 1
    assert client.calls[0]["url"] == f"{DEFAULT_OLLAMA_BASE_URL}{OLLAMA_EMBED_PATH}"
    assert client.calls[0]["json"] == {
        "model": "nomic-embed-text",
        "input": "hello world",
    }


def test_embed_texts_batches_multiple_texts_in_one_request(
    provider: OllamaEmbeddingProvider,
) -> None:
    client = provider._client
    assert isinstance(client, FakeOllamaClient)
    vectors = provider.embed_texts(["first text", "second text"])

    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert len(client.calls) == 1
    assert client.calls[0]["json"]["input"] == ["first text", "second text"]


def test_embed_texts_returns_empty_list_for_empty_input(
    provider: OllamaEmbeddingProvider,
) -> None:
    assert provider.embed_texts([]) == []


def test_embed_texts_returns_zero_vectors_for_blank_inputs() -> None:
    client = FakeOllamaClient(vectors=[[0.5, 0.6]])
    provider = OllamaEmbeddingProvider(
        model="nomic-embed-text",
        dimension=2,
        client=client,
    )

    vectors = provider.embed_texts(["   ", "valid text"])

    assert vectors[0] == [0.0, 0.0]
    assert vectors[1] == [0.5, 0.6]
    assert client.calls[0]["json"]["input"] == "valid text"


def test_http_error_is_translated_to_embedding_provider_error() -> None:
    client = FakeOllamaClient(error=httpx.ConnectError("connection refused"))
    provider = OllamaEmbeddingProvider(
        dimension=3,
        client=client,
    )

    with pytest.raises(EmbeddingProviderError, match="Ollama embedding request failed"):
        provider.embed("failure case")


def test_http_status_error_is_translated_to_embedding_provider_error() -> None:
    client = FakeOllamaClient(status_code=500)
    provider = OllamaEmbeddingProvider(
        dimension=3,
        client=client,
    )

    with pytest.raises(EmbeddingProviderError, match="HTTP 500"):
        provider.embed("failure case")


def test_invalid_embedding_dimensions_raise_application_error() -> None:
    client = FakeOllamaClient(vectors=[[0.1, 0.2]])
    provider = OllamaEmbeddingProvider(
        dimension=3,
        client=client,
    )

    with pytest.raises(InvalidEmbeddingDimensionError):
        provider.embed("dimension mismatch")


def test_missing_embeddings_field_raises_embedding_provider_error() -> None:
    class InvalidResponseClient:
        def post(self, url: str, *, json: dict[str, object]) -> SimpleNamespace:
            return SimpleNamespace(status_code=200, json=lambda: {"model": "nomic-embed-text"})

    provider = OllamaEmbeddingProvider(
        dimension=3,
        client=InvalidResponseClient(),
    )

    with pytest.raises(EmbeddingProviderError, match="missing embeddings field"):
        provider.embed("invalid response")
