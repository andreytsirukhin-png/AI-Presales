from typing import Any, Protocol

import chromadb

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.chroma_metadata import (
    metadata_from_chroma,
    metadata_to_chroma,
)
from app.infrastructure.vector_store.similarity import cosine_similarity
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.index import IndexedChunk
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.schemas.source_metadata import SourceMetadata

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
                metadata_to_chroma(embedding.metadata)
                if embedding.metadata
                else {
                    "document_id": document_id,
                    "chunk_index": embedding.index,
                    "document_name": document_id,
                    "chunk_id": f"{document_id}-chunk-{embedding.index}",
                    "embedding_model": "unknown",
                    "created_at": "",
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
            metadata = metadatas[index]
            chunk_index = int(metadata["chunk_index"])
            distance = float(distances[index])
            score = 1.0 - distance
            results.append(
                SearchResult(
                    chunk_index=chunk_index,
                    text=documents[index] or "",
                    score=score,
                    metadata=ChromaVectorStore._metadata_from_record(metadata),
                )
            )

        return sorted(results, key=lambda result: (-result.score, result.chunk_index))

    def count_documents(self, document_ids: list[str]) -> int:
        """Return indexed chunk count across the given documents."""
        if not document_ids:
            return 0
        collection = self._collection_or_create()
        total = 0
        for document_id in document_ids:
            payload = collection.get(where={"document_id": document_id})
            total += len(payload.get("ids", []))
        return total

    def search_documents(
        self,
        document_ids: list[str],
        query_vector: list[float],
        top_k: int,
    ) -> list[SearchResult]:
        """Search indexed chunks across multiple documents using Chroma."""
        if not document_ids:
            return []

        collection = self._collection_or_create()
        indexed_ids = [
            document_id
            for document_id in document_ids
            if self._document_exists(document_id)
        ]
        if not indexed_ids:
            raise DocumentNotFoundError("No indexed documents found for project search.")

        stored = collection.get(
            where={"document_id": indexed_ids[0]},
            include=["embeddings"],
            limit=1,
        )
        cosine_similarity(query_vector, stored["embeddings"][0])

        response = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"document_id": {"$in": indexed_ids}},
            include=["documents", "distances", "metadatas"],
        )

        results: list[SearchResult] = []
        ids = response.get("ids", [[]])[0]
        documents = response.get("documents", [[]])[0]
        distances = response.get("distances", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]

        for index, _chunk_id in enumerate(ids):
            metadata = metadatas[index]
            chunk_index = int(metadata["chunk_index"])
            distance = float(distances[index])
            score = 1.0 - distance
            results.append(
                SearchResult(
                    chunk_index=chunk_index,
                    text=documents[index] or "",
                    score=score,
                    metadata=ChromaVectorStore._metadata_from_record(metadata),
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
                    metadata=ChromaVectorStore._metadata_from_record(metadata),
                )
            )
        return sorted(chunks, key=lambda chunk: chunk.index)

    @staticmethod
    def _metadata_from_record(metadata: dict[str, object] | None) -> SourceMetadata | None:
        if not metadata:
            return None
        if "document_name" in metadata:
            return metadata_from_chroma(metadata)

        document_id = metadata.get("document_id")
        chunk_index_raw = metadata.get("chunk_index")
        if document_id is None or chunk_index_raw is None:
            return None

        from app.modules.documents.schemas.source_metadata import build_chunk_id

        document_id_str = str(document_id)
        chunk_index = int(chunk_index_raw)
        page_raw = metadata.get("page_number")
        page_number = int(page_raw) if page_raw is not None else None
        return SourceMetadata(
            document_id=document_id_str,
            document_name=str(metadata.get("document_name") or document_id_str),
            page_number=page_number,
            chunk_id=str(metadata.get("chunk_id") or build_chunk_id(document_id_str, chunk_index)),
            chunk_index=chunk_index,
            embedding_model=str(metadata.get("embedding_model") or "unknown"),
            created_at=str(metadata.get("created_at") or ""),
        )
