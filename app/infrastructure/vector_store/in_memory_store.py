from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.similarity import cosine_similarity
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk
from app.modules.documents.schemas.search import SearchResult


class InMemoryVectorStore:
    """Non-persistent in-memory vector store for development and tests."""

    def __init__(self) -> None:
        self._store: dict[str, list[IndexedChunk]] = {}

    def upsert(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        self._store[document_id] = [
            IndexedChunk(
                index=embedding.index,
                text=embedding.text,
                vector=embedding.vector,
            )
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

    def search(
        self,
        document_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Rank indexed chunks by cosine similarity to the query vector.

        Args:
            document_id: Identifier of the indexed document to search.
            query_vector: Embedding vector for the query text.
            top_k: Maximum number of ranked results to return.

        Returns:
            Ranked search results scoped to the requested document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        indexed_chunks = self.get(document_id)

        ranked_results = sorted(
            (
                SearchResult(
                    chunk_index=chunk.index,
                    text=chunk.text,
                    score=cosine_similarity(query_vector, chunk.vector),
                )
                for chunk in indexed_chunks
            ),
            key=lambda result: (-result.score, result.chunk_index),
        )

        return ranked_results[:top_k]
