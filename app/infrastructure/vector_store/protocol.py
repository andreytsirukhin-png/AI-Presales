from typing import Protocol

from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk


class VectorStore(Protocol):
    """Abstraction for storing and retrieving document embedding vectors."""

    def upsert(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        ...

    def get(self, document_id: str) -> list[IndexedChunk]:
        """Return stored embeddings for a document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
        """
        ...
