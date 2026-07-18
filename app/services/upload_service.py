from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.infrastructure.storage.protocol import FileStorage
from app.models.document import UploadResponse
from app.modules.documents.schemas.document import DocumentMetadata

ALLOWED_EXTENSION = ".pdf"
PDF_MAGIC_BYTES = b"%PDF"
DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class UploadService:
    """Validates and persists uploaded PDF documents."""

    def __init__(
        self,
        storage: FileStorage,
        *,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    ) -> None:
        self._storage = storage
        self._max_upload_bytes = max_upload_bytes

    def upload(
        self,
        filename: str | None,
        content: bytes,
        *,
        content_type: str | None = None,
    ) -> UploadResponse:
        """Validate an uploaded PDF and persist it to storage.

        Args:
            filename: Original client filename.
            content: Raw file bytes.
            content_type: MIME type reported by the client.

        Returns:
            Upload metadata including a generated document identifier.

        Raises:
            UnsupportedFileTypeError: If the file is not a valid PDF.
            FileTooLargeError: If the file exceeds the configured size limit.
        """
        original_filename = filename or "document.pdf"
        suffix = Path(original_filename).suffix.lower()

        if suffix != ALLOWED_EXTENSION:
            raise UnsupportedFileTypeError(
                f"Unsupported file type. Only PDF files are allowed."
            )

        if not content.startswith(PDF_MAGIC_BYTES):
            raise UnsupportedFileTypeError(
                "Unsupported file type. Only PDF files are allowed."
            )

        if len(content) > self._max_upload_bytes:
            raise FileTooLargeError("File exceeds 25 MB limit.")

        document_id = str(uuid4())
        storage_path = f"{document_id}{ALLOWED_EXTENSION}"
        self._storage.save(storage_path, content)
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
            )
        )

        return UploadResponse(
            document_id=document_id,
            filename=original_filename,
            status="uploaded",
        )
