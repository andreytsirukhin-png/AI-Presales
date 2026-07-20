from typing import Protocol

from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk
from app.modules.documents.schemas.search import SearchResult


class VectorStore(Protocol):
    """Abstraction for storing and retrieving document embedding vectors."""

    def create_collection(self) -> None:
        """Ensure the backing collection or storage namespace exists."""
        ...

    def add_documents(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        ...

    def upsert(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        ...

    def get(self, document_id: str) -> list[IndexedChunk]:
        """Return stored embeddings for a document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
        """
        ...

    def search(
        self,
        document_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Search indexed chunks within a single document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        ...

    def delete_document(self, document_id: str) -> None:
        """Remove all indexed chunks for a document."""
        ...

    def clear(self) -> None:
        """Remove all indexed chunks from the store."""
        ...

    def count(self) -> int:
        """Return the total number of indexed chunks in the store."""
        ...

    def count_documents(self, document_ids: list[str]) -> int:
        """Return indexed chunk count across the given documents."""
        ...

    def search_documents(
        self,
        document_ids: list[str],
        query_vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Search indexed chunks across multiple documents.

        Raises:
            DocumentNotFoundError: If none of the documents are indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        ...
