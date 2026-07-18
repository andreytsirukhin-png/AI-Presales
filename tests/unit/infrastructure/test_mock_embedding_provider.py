import pytest

from app.infrastructure.embeddings.mock_provider import (
    MOCK_EMBEDDING_DIMENSION,
    MockEmbeddingProvider,
)


@pytest.fixture
def provider() -> MockEmbeddingProvider:
    return MockEmbeddingProvider()


def test_dimension_is_sixteen(provider: MockEmbeddingProvider) -> None:
    assert provider.dimension == MOCK_EMBEDDING_DIMENSION


def test_embed_returns_float_vector_with_expected_dimension(
    provider: MockEmbeddingProvider,
) -> None:
    vector = provider.embed("sample text")

    assert len(vector) == MOCK_EMBEDDING_DIMENSION
    assert all(isinstance(value, float) for value in vector)


def test_embed_is_deterministic_for_same_input(provider: MockEmbeddingProvider) -> None:
    text = "deterministic embedding input"

    first = provider.embed(text)
    second = provider.embed(text)

    assert first == second


def test_embed_returns_different_vectors_for_different_input(
    provider: MockEmbeddingProvider,
) -> None:
    first = provider.embed("first input")
    second = provider.embed("second input")

    assert first != second
