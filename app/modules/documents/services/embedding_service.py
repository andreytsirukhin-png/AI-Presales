from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.modules.documents.schemas.embedding import Embedding, EmbeddingResponse
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.metadata_service import MetadataService


class EmbeddingService:
    """Generates embeddings for stored document chunks."""

    def __init__(
        self,
        metadata_service: MetadataService,
        chunk_service: ChunkService,
        provider: EmbeddingProvider,
    ) -> None:
        self._metadata_service = metadata_service
        self._chunk_service = chunk_service
        self._provider = provider

    def embed(self, document_id: str) -> EmbeddingResponse:
        """Validate, chunk, and embed a stored document.

        Args:
            document_id: Identifier returned by the upload endpoint.

        Returns:
            Summary of generated embeddings for the document.

        Raises:
            DocumentNotFoundError: If the document or its metadata does not exist.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        self._metadata_service.get(document_id)
        chunk_response = self._chunk_service.chunk(document_id)

        embeddings = [
            Embedding(index=chunk.index, vector=self._provider.embed(chunk.text))
            for chunk in chunk_response.chunks
        ]

        return EmbeddingResponse(
            document_id=document_id,
            chunk_count=len(embeddings),
            embedding_dimension=self._provider.dimension,
            status="embedded",
        )
