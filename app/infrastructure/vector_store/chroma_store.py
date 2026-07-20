from typing import Any, Protocol

import chromadb

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.similarity import cosine_similarity
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk
from app.modules.documents.schemas.search import SearchResult

DEFAULT_COLLECTION_NAME = "ai-presales"
COSINE_SPACE_METADATA = {"hnsw:space": "cosine"}


class ChromaClientProtocol(Protocol):
    """Minimal Chroma client surface required for persistence."""

    def get_or_create_collection(
        self,
        name: str,
        *,
        metadata: dict[str, str] | None = None,
    ) -> Any:
        """Return an existing collection or create a new one."""
        ...

    def delete_collection(self, name: str) -> None:
        """Delete a collection by name."""
        ...


class ChromaVectorStore:
    """Persistent ChromaDB-backed vector store."""

    def __init__(
        self,
        persist_path: str,
        *,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        client: ChromaClientProtocol | None = None,
    ) -> None:
        """Initialize a persistent Chroma vector store.

        Args:
            persist_path: Directory path for Chroma persistence.
            collection_name: Name of the Chroma collection.
            client: Optional injected Chroma client for testing.
        """
        self._persist_path = persist_path
        self._collection_name = collection_name
        self._client = client or chromadb.PersistentClient(path=persist_path)
        self._collection: Any | None = None

    def create_collection(self) -> None:
        """Ensure the Chroma collection exists."""
        self._collection = self._client.get_or_create_collection(
            name=self._collection_name,
            metadata=COSINE_SPACE_METADATA,
        )

    def add_documents(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        self.delete_document(document_id)
        if not embeddings:
            return

        collection = self._collection_or_create()
        collection.add(
            ids=[self._chunk_id(document_id, embedding.index) for embedding in embeddings],
            embeddings=[embedding.vector for embedding in embeddings],
            documents=[embedding.text for embedding in embeddings],
            metadatas=[
                {
                    "document_id": document_id,
                    "chunk_index": embedding.index,
                }
                for embedding in embeddings
            ],
        )

    def upsert(self, document_id: str, embeddings: list[Embedding]) -> None:
        """Insert or replace embeddings for a document."""
        self.add_documents(document_id, embeddings)

    def get(self, document_id: str) -> list[IndexedChunk]:
        """Return stored embeddings for a document.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
        """
        collection = self._collection_or_create()
        payload = collection.get(
            where={"document_id": document_id},
            include=["embeddings", "documents", "metadatas"],
        )
        if not payload["ids"]:
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        return self._indexed_chunks_from_payload(payload)

    def search(
        self,
        document_id: str,
        query_vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Search indexed chunks within a single document using Chroma.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        collection = self._collection_or_create()
        if not self._document_exists(document_id):
            raise DocumentNotFoundError(f"Document not found: {document_id}")

        stored = collection.get(
            where={"document_id": document_id},
            include=["embeddings"],
            limit=1,
        )
        stored_vector = stored["embeddings"][0]
        cosine_similarity(query_vector, stored_vector)

        response = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"document_id": document_id},
            include=["documents", "distances", "metadatas"],
        )

        results: list[SearchResult] = []
        ids = response.get("ids", [[]])[0]
        documents = response.get("documents", [[]])[0]
        distances = response.get("distances", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]

        for index, chunk_id in enumerate(ids):
            chunk_index = int(metadatas[index]["chunk_index"])
            distance = float(distances[index])
            score = 1.0 - distance
            results.append(
                SearchResult(
                    chunk_index=chunk_index,
                    text=documents[index] or "",
                    score=score,
                )
            )

        return sorted(results, key=lambda result: (-result.score, result.chunk_index))

    def delete_document(self, document_id: str) -> None:
        """Remove all indexed chunks for a document."""
        collection = self._collection_or_create()
        payload = collection.get(where={"document_id": document_id})
        if payload["ids"]:
            collection.delete(ids=payload["ids"])

    def clear(self) -> None:
        """Remove all indexed chunks from the store."""
        try:
            self._client.delete_collection(self._collection_name)
        except Exception:
            pass
        self._collection = None
        self.create_collection()

    def count(self) -> int:
        """Return the total number of indexed chunks in the store."""
        collection = self._collection_or_create()
        return int(collection.count())

    def _collection_or_create(self) -> Any:
        if self._collection is None:
            self.create_collection()
        return self._collection

    def _document_exists(self, document_id: str) -> bool:
        collection = self._collection_or_create()
        payload = collection.get(where={"document_id": document_id}, limit=1)
        return bool(payload["ids"])

    @staticmethod
    def _chunk_id(document_id: str, chunk_index: int) -> str:
        return f"{document_id}:{chunk_index}"

    @staticmethod
    def _indexed_chunks_from_payload(payload: dict[str, Any]) -> list[IndexedChunk]:
        chunks: list[IndexedChunk] = []
        for index, chunk_id in enumerate(payload["ids"]):
            metadata = payload["metadatas"][index]
            chunks.append(
                IndexedChunk(
                    index=int(metadata["chunk_index"]),
                    text=payload["documents"][index] or "",
                    vector=list(payload["embeddings"][index]),
                )
            )
        return sorted(chunks, key=lambda chunk: chunk.index)
