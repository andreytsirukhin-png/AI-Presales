from types import SimpleNamespace

import pytest
from openai import OpenAIError

from app.core.exceptions import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    InvalidEmbeddingDimensionError,
)
from app.infrastructure.embeddings.openai_provider import OpenAIEmbeddingProvider


class FakeEmbeddingsAPI:
    """Test double for the OpenAI embeddings API."""

    def __init__(
        self,
        *,
        vectors: list[list[float]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.vectors = vectors or [[0.1, 0.2, 0.3]]
        self.error = error
        self.calls: list[dict[str, object]] = []

    def create(
        self,
        *,
        input: list[str],
        model: str,
        dimensions: int | None = None,
    ) -> SimpleNamespace:
        self.calls.append(
            {"input": input, "model": model, "dimensions": dimensions}
        )
        if self.error is not None:
            raise self.error
        if len(self.vectors) == 1 and len(input) > 1:
            response_vectors = [self.vectors[0] for _ in input]
        else:
            response_vectors = self.vectors
        return SimpleNamespace(
            data=[
                SimpleNamespace(embedding=vector, index=index)
                for index, vector in enumerate(response_vectors)
            ]
        )


class FakeOpenAIClient:
    """Test double for an OpenAI client."""

    def __init__(self, embeddings_api: FakeEmbeddingsAPI) -> None:
        self.embeddings = embeddings_api


@pytest.fixture
def provider() -> OpenAIEmbeddingProvider:
    embeddings_api = FakeEmbeddingsAPI(vectors=[[0.1, 0.2, 0.3]])
    client = FakeOpenAIClient(embeddings_api)
    return OpenAIEmbeddingProvider(
        api_key="test-key",
        model="text-embedding-3-small",
        dimension=3,
        client=client,
    )


def test_embed_returns_vector_for_single_text(provider: OpenAIEmbeddingProvider) -> None:
    vector = provider.embed("hello world")

    assert vector == [0.1, 0.2, 0.3]


def test_embed_texts_batches_multiple_texts_in_one_request(
    provider: OpenAIEmbeddingProvider,
) -> None:
    embeddings_api = provider._client.embeddings
    vectors = provider.embed_texts(["first text", "second text"])

    assert vectors == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert len(embeddings_api.calls) == 1
    assert embeddings_api.calls[0]["input"] == ["first text", "second text"]
    assert embeddings_api.calls[0]["dimensions"] == 3


def test_embed_texts_requests_configured_dimensions_for_embedding_v3_models() -> None:
    embeddings_api = FakeEmbeddingsAPI(vectors=[[0.4, 0.5, 0.6, 0.7]])
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        model="text-embedding-3-small",
        dimension=4,
        client=FakeOpenAIClient(embeddings_api),
    )

    provider.embed_texts(["dimension config test"])

    assert embeddings_api.calls[0]["dimensions"] == 4


def test_embed_texts_returns_empty_list_for_empty_input(
    provider: OpenAIEmbeddingProvider,
) -> None:
    assert provider.embed_texts([]) == []


def test_embed_texts_returns_zero_vectors_for_blank_inputs() -> None:
    embeddings_api = FakeEmbeddingsAPI(vectors=[[0.5, 0.6]])
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        dimension=2,
        client=FakeOpenAIClient(embeddings_api),
    )

    vectors = provider.embed_texts(["   ", "valid text"])

    assert vectors[0] == [0.0, 0.0]
    assert vectors[1] == [0.5, 0.6]
    assert embeddings_api.calls[0]["input"] == ["valid text"]


def test_missing_api_key_raises_configuration_error() -> None:
    with pytest.raises(EmbeddingConfigurationError):
        OpenAIEmbeddingProvider(api_key="", dimension=3)


def test_api_error_is_translated_to_embedding_provider_error() -> None:
    embeddings_api = FakeEmbeddingsAPI(error=OpenAIError("boom"))
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        dimension=3,
        client=FakeOpenAIClient(embeddings_api),
    )

    with pytest.raises(EmbeddingProviderError, match="OpenAI embedding request failed"):
        provider.embed("failure case")


def test_invalid_embedding_dimensions_raise_application_error() -> None:
    embeddings_api = FakeEmbeddingsAPI(vectors=[[0.1, 0.2]])
    provider = OpenAIEmbeddingProvider(
        api_key="test-key",
        dimension=3,
        client=FakeOpenAIClient(embeddings_api),
    )

    with pytest.raises(InvalidEmbeddingDimensionError):
        provider.embed("dimension mismatch")
