from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.storage.protocol import FileStorage
from app.modules.documents.schemas.document import DocumentMetadata


class MetadataService:
    """Retrieves and updates persisted document metadata from storage."""

    def __init__(self, storage: FileStorage) -> None:
        self._storage = storage

    def get(self, document_id: str) -> DocumentMetadata:
        """Return metadata for a stored document.

        Raises:
            DocumentNotFoundError: If no metadata exists for the given identifier.
        """
        try:
            return self._storage.get_metadata(document_id)
        except FileNotFoundError as exc:
            raise DocumentNotFoundError(
                f"Document not found: {document_id}"
            ) from exc

    def save(self, metadata: DocumentMetadata) -> None:
        """Persist document metadata."""
        self._storage.save_metadata(metadata)
