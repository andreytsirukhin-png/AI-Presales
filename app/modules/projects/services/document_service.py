from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    ProjectNotFoundError,
    UnsupportedFileTypeError,
)
from app.infrastructure.storage.local_storage import LocalFileStorage
from app.infrastructure.storage.protocol import FileStorage
from app.infrastructure.vector_store.protocol import VectorStore
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.projects.schemas.document import (
    ProjectDocumentListResponse,
    ProjectDocumentUploadResponse,
)
from app.modules.projects.services.project_service import ProjectService
from app.services.upload_service import ALLOWED_EXTENSION, PDF_MAGIC_BYTES, UploadService


class ProjectDocumentService:
    """Uploads, lists, and removes documents within a project workspace."""

    def __init__(
        self,
        storage: FileStorage,
        project_service: ProjectService,
        metadata_service: MetadataService,
        index_service: IndexService,
        vector_store: VectorStore,
        *,
        max_upload_bytes: int,
    ) -> None:
        self._storage = storage
        self._project_service = project_service
        self._metadata_service = metadata_service
        self._index_service = index_service
        self._vector_store = vector_store
        self._upload_service = UploadService(storage, max_upload_bytes=max_upload_bytes)

    def upload_and_index(
        self,
        project_id: str,
        filename: str | None,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> ProjectDocumentUploadResponse:
        """Upload a PDF into a project and run the full indexing pipeline."""
        self._project_service.require_metadata(project_id)
        original_filename = filename or "document.pdf"
        suffix = Path(original_filename).suffix.lower()
        if suffix != ALLOWED_EXTENSION:
            raise UnsupportedFileTypeError("Unsupported file type. Only PDF files are allowed.")
        if not content.startswith(PDF_MAGIC_BYTES):
            raise UnsupportedFileTypeError("Unsupported file type. Only PDF files are allowed.")
        if len(content) > self._upload_service._max_upload_bytes:
            raise FileTooLargeError("File exceeds 25 MB limit.")

        document_id = str(uuid4())
        self._storage.save(f"{document_id}{ALLOWED_EXTENSION}", content)
        self._storage.save_metadata(
            DocumentMetadata(
                document_id=document_id,
                filename=original_filename,
                content_type=content_type or "application/pdf",
                size_bytes=len(content),
                status="uploaded",
                page_count=None,
                characters=None,
                created_at=datetime.now(UTC),
                project_id=project_id,
            )
        )
        self._project_service.attach_document(project_id, document_id)

        index_response = self._index_service.index(document_id)
        indexed_at = datetime.now(UTC)
        document_metadata = self._metadata_service.get(document_id).model_copy(
            update={
                "chunks_indexed": index_response.chunks_indexed,
                "indexed_at": indexed_at,
            }
        )
        self._metadata_service.save(document_metadata)
        self._project_service.mark_indexed(project_id, indexed_at)

        return ProjectDocumentUploadResponse(
            project_id=project_id,
            document_id=document_id,
            filename=original_filename,
            status="indexed",
            chunks_indexed=index_response.chunks_indexed,
        )

    def list_documents(self, project_id: str) -> ProjectDocumentListResponse:
        """Return metadata for all documents in a project."""
        project = self._project_service.require_metadata(project_id)
        documents: list[DocumentMetadata] = []
        for document_id in project.document_ids:
            try:
                documents.append(self._metadata_service.get(document_id))
            except DocumentNotFoundError:
                continue
        return ProjectDocumentListResponse(
            project_id=project_id,
            documents=documents,
            count=len(documents),
        )

    def delete_document(self, project_id: str, document_id: str) -> None:
        """Remove a document from a project, storage, and the vector index."""
        project = self._project_service.require_metadata(project_id)
        if document_id not in project.document_ids:
            raise DocumentNotFoundError(
                f"Document not found in project: {document_id}"
            )

        self._vector_store.delete_document(document_id)
        if isinstance(self._storage, LocalFileStorage):
            self._storage.delete_document_files(document_id)
        self._project_service.detach_document(project_id, document_id)
