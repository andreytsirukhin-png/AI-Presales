from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.index import IndexResponse
from app.modules.documents.services.embedding_service import EmbeddingService


class IndexService:
    """Indexes generated document embeddings in a vector store."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_service = embedding_service
        self._vector_store = vector_store

    def index(self, document_id: str) -> IndexResponse:
        """Generate embeddings and store them for a document.

        Args:
            document_id: Identifier returned by the upload endpoint.

        Returns:
            Summary of indexed chunks for the document.

        Raises:
            DocumentNotFoundError: If the document or its metadata does not exist.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        embeddings = self._embedding_service.generate_embeddings(document_id)
        self._vector_store.upsert(document_id, embeddings)

        return IndexResponse(
            document_id=document_id,
            chunks_indexed=len(embeddings),
            status="indexed",
        )
