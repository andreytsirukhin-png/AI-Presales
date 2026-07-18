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

    def generate_embeddings(self, document_id: str) -> list[Embedding]:
        """Validate, chunk, and generate embeddings for a stored document.

        Args:
            document_id: Identifier returned by the upload endpoint.

        Returns:
            Generated embeddings for each document chunk.

        Raises:
            DocumentNotFoundError: If the document or its metadata does not exist.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        self._metadata_service.get(document_id)
        chunk_response = self._chunk_service.chunk(document_id)
        vectors = self._embed_chunk_texts([chunk.text for chunk in chunk_response.chunks])

        return [
            Embedding(
                index=chunk.index,
                text=chunk.text,
                vector=vector,
            )
            for chunk, vector in zip(chunk_response.chunks, vectors)
        ]

    def _embed_chunk_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed chunk texts using the configured provider."""
        return self._provider.embed_texts(texts)

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
        embeddings = self.generate_embeddings(document_id)

        return EmbeddingResponse(
            document_id=document_id,
            chunk_count=len(embeddings),
            embedding_dimension=self._provider.dimension,
            status="embedded",
        )
