from typing import Protocol


class EmbeddingProvider(Protocol):
    """Abstraction for generating vector embeddings from text."""

    @property
    def dimension(self) -> int:
        """Return the number of dimensions in generated vectors."""
        ...

    def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        ...
