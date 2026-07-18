from typing import Protocol

from openai import OpenAI, OpenAIError

from app.core.exceptions import (
    EmbeddingConfigurationError,
    EmbeddingProviderError,
    InvalidEmbeddingDimensionError,
)

DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"


class OpenAIClientProtocol(Protocol):
    """Minimal OpenAI client surface required for embedding generation."""

    class Embeddings:
        def create(
            self,
            *,
            input: list[str],
            model: str,
            dimensions: int | None = None,
        ) -> object: ...

    embeddings: Embeddings


class OpenAIEmbeddingProvider:
    """OpenAI-backed embedding provider with batched requests."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEFAULT_OPENAI_EMBEDDING_MODEL,
        dimension: int,
        client: OpenAIClientProtocol | None = None,
    ) -> None:
        """Initialize the OpenAI embedding provider.

        Args:
            api_key: OpenAI API key.
            model: Embedding model name.
            dimension: Expected embedding vector size.
            client: Optional injected OpenAI client for testing.

        Raises:
            EmbeddingConfigurationError: If the API key is missing.
        """
        if not api_key.strip():
            raise EmbeddingConfigurationError(
                "OpenAI API key is required when embedding_provider is 'openai'."
            )

        self._model = model
        self._dimension = dimension
        self._client = client or OpenAI(api_key=api_key)

    @property
    def dimension(self) -> int:
        """Return the configured embedding vector size."""
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text input."""
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts in one request.

        Args:
            texts: Ordered text inputs to embed.

        Returns:
            Embedding vectors in the same order as the input texts.
        """
        if not texts:
            return []

        vectors: list[list[float]] = [[0.0] * self._dimension for _ in texts]
        batch_texts: list[str] = []
        batch_indices: list[int] = []

        for index, text in enumerate(texts):
            if text.strip():
                batch_indices.append(index)
                batch_texts.append(text)

        if not batch_texts:
            return vectors

        try:
            request_kwargs: dict[str, object] = {
                "input": batch_texts,
                "model": self._model,
            }
            if self._model.startswith("text-embedding-3"):
                request_kwargs["dimensions"] = self._dimension
            response = self._client.embeddings.create(**request_kwargs)
        except OpenAIError as exc:
            raise EmbeddingProviderError(
                f"OpenAI embedding request failed: {exc}"
            ) from exc

        ordered_items = sorted(response.data, key=lambda item: item.index)
        if len(ordered_items) != len(batch_texts):
            raise EmbeddingProviderError(
                "OpenAI embedding response count does not match request count."
            )

        for batch_index, item in enumerate(ordered_items):
            vector = list(item.embedding)
            if len(vector) != self._dimension:
                raise InvalidEmbeddingDimensionError(
                    "OpenAI embedding dimension mismatch: "
                    f"expected {self._dimension}, got {len(vector)}"
                )
            vectors[batch_indices[batch_index]] = vector

        return vectors
