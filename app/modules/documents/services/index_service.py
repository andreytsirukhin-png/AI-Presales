from datetime import UTC, datetime

from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.index import IndexResponse
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.projects.services.project_service import ProjectService


class IndexService:
    """Indexes generated document embeddings in a vector store."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        metadata_service: MetadataService | None = None,
        project_service: ProjectService | None = None,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._metadata_service = metadata_service
        self._project_service = project_service

    def index(self, document_id: str) -> IndexResponse:
        """Generate embeddings and store them for a document."""
        embeddings = self._embedding_service.generate_embeddings(document_id)
        self._vector_store.add_documents(document_id, embeddings)

        indexed_at = datetime.now(UTC)
        if self._metadata_service is not None:
            document_metadata = self._metadata_service.get(document_id)
            self._metadata_service.save(
                document_metadata.model_copy(
                    update={
                        "chunks_indexed": len(embeddings),
                        "indexed_at": indexed_at,
                    }
                )
            )
            if document_metadata.project_id and self._project_service is not None:
                self._project_service.mark_indexed(document_metadata.project_id, indexed_at)

        return IndexResponse(
            document_id=document_id,
            chunks_indexed=len(embeddings),
            status="indexed",
        )
