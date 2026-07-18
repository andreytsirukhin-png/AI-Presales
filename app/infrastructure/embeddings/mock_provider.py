import hashlib

MOCK_EMBEDDING_DIMENSION = 16


class MockEmbeddingProvider:
    """Deterministic in-memory embedding provider for development and tests."""

    def __init__(self, dimension: int = MOCK_EMBEDDING_DIMENSION) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        """Return the configured embedding vector size."""
        return self._dimension

    def embed(self, text: str) -> list[float]:
        """Generate a deterministic float vector for the given text.

        Args:
            text: Source text to embed.

        Returns:
            A float vector of length ``dimension``.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector: list[float] = []

        for index in range(self._dimension):
            byte_offset = (index * 2) % len(digest)
            raw_value = int.from_bytes(digest[byte_offset : byte_offset + 2], "big")
            vector.append(raw_value / 65535.0)

        return vector

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts."""
        return [self.embed(text) for text in texts]
