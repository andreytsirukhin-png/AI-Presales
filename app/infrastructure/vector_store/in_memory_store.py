from app.core.exceptions import DocumentNotFoundError
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk


class InMemoryVectorStore:
    """Non-persistent in-memory vector store for development and tests."""

    def __init__(self) -> None:
        self._store: dict[str, list[IndexedChunk]] = {}

    def upsert(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        self._store[document_id] = [
            IndexedChunk(index=embedding.index, vector=embedding.vector)
            for embedding in embeddings
        ]

    def get(self, document_id: str) -> list[IndexedChunk]:
        """Return stored embeddings for a document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
        """
        try:
            return self._store[document_id]
        except KeyError as exc:
            raise DocumentNotFoundError(
                f"Document not found: {document_id}"
            ) from exc
