from datetime import UTC, datetime

from app.core.config import Settings
from app.infrastructure.embeddings.protocol import EmbeddingProvider
from app.modules.documents.schemas.embedding import Embedding, EmbeddingResponse
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.citations import metadata_from_stored
from app.infrastructure.storage.project_storage import ProjectStorage
from app.modules.documents.services.metadata_service import MetadataService


def resolve_embedding_model(settings: Settings) -> str:
    """Return the configured embedding model label for metadata storage."""
    if settings.embedding_provider == "openai":
        return settings.openai_embedding_model
    if settings.embedding_provider == "ollama":
        return settings.ollama_embedding_model
    return "mock"


class EmbeddingService:
    """Generates embeddings for stored document chunks."""

    def __init__(
        self,
        metadata_service: MetadataService,
        chunk_service: ChunkService,
        provider: EmbeddingProvider,
        *,
        embedding_model: str,
        project_storage: ProjectStorage | None = None,
    ) -> None:
        self._metadata_service = metadata_service
        self._chunk_service = chunk_service
        self._provider = provider
        self._embedding_model = embedding_model
        self._project_storage = project_storage

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
        document_metadata = self._metadata_service.get(document_id)
        chunk_response = self._chunk_service.chunk(document_id)
        vectors = self._embed_chunk_texts([chunk.text for chunk in chunk_response.chunks])
        created_at = datetime.now(UTC).isoformat()
        project_id = document_metadata.project_id
        project_name = self._resolve_project_name(project_id)

        return [
            Embedding(
                index=chunk.index,
                text=chunk.text,
                vector=vector,
                metadata=metadata_from_stored(
                    document_id=document_id,
                    document_name=document_metadata.filename,
                    chunk_index=chunk.index,
                    embedding_model=self._embedding_model,
                    created_at=created_at,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    heading=chunk.heading,
                    project_id=project_id,
                    project_name=project_name,
                ),
            )
            for chunk, vector in zip(chunk_response.chunks, vectors)
        ]

    def _resolve_project_name(self, project_id: str | None) -> str | None:
        if not project_id or self._project_storage is None:
            return None
        try:
            return self._project_storage.get(project_id).project_name
        except FileNotFoundError:
            return None

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
