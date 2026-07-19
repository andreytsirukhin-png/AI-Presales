from typing import Protocol

import httpx

from app.core.exceptions import EmbeddingProviderError, InvalidEmbeddingDimensionError

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 30.0
OLLAMA_EMBED_PATH = "/api/embed"


class OllamaClientProtocol(Protocol):
    """Minimal HTTP client surface required for Ollama embedding requests."""

    def post(self, url: str, *, json: dict[str, object]) -> httpx.Response:
        """Execute an HTTP POST request."""
        ...


class OllamaEmbeddingProvider:
    """Ollama-backed embedding provider using POST /api/embed."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_OLLAMA_BASE_URL,
        model: str = DEFAULT_OLLAMA_EMBEDDING_MODEL,
        dimension: int,
        timeout_seconds: float = DEFAULT_OLLAMA_TIMEOUT_SECONDS,
        client: OllamaClientProtocol | None = None,
    ) -> None:
        """Initialize the Ollama embedding provider.

        Args:
            base_url: Ollama server base URL.
            model: Embedding model name served by Ollama.
            dimension: Expected embedding vector size.
            timeout_seconds: HTTP request timeout in seconds.
            client: Optional injected HTTP client for testing.
        """
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._dimension = dimension
        self._timeout_seconds = timeout_seconds
        self._client = client

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
            response_vectors = self._request_embeddings(batch_texts)
        except httpx.HTTPError as exc:
            raise EmbeddingProviderError(
                f"Ollama embedding request failed: {exc}"
            ) from exc

        if len(response_vectors) != len(batch_texts):
            raise EmbeddingProviderError(
                "Ollama embedding response count does not match request count."
            )

        for batch_index, vector in enumerate(response_vectors):
            if len(vector) != self._dimension:
                raise InvalidEmbeddingDimensionError(
                    "Ollama embedding dimension mismatch: "
                    f"expected {self._dimension}, got {len(vector)}"
                )
            vectors[batch_indices[batch_index]] = vector

        return vectors

    def _request_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Call Ollama's embed API for one or more texts."""
        payload: dict[str, object] = {
            "model": self._model,
            "input": texts[0] if len(texts) == 1 else texts,
        }
        url = f"{self._base_url}{OLLAMA_EMBED_PATH}"

        if self._client is not None:
            response = self._client.post(url, json=payload)
        else:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                response = client.post(url, json=payload)

        if response.status_code >= 400:
            raise EmbeddingProviderError(
                f"Ollama embedding request failed: HTTP {response.status_code}"
            )

        body = response.json()
        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list):
            raise EmbeddingProviderError(
                "Ollama embedding response missing embeddings field."
            )

        return [list(vector) for vector in embeddings]
