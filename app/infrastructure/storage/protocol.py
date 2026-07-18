from typing import Protocol

from app.modules.documents.schemas.document import DocumentMetadata


class FileStorage(Protocol):
    """Abstraction for persisting and loading document bytes and metadata."""

    def save(self, relative_path: str, content: bytes) -> None:
        """Persist content at the given path relative to the storage root."""
        ...

    def load(self, relative_path: str) -> bytes:
        """Load content from the given path relative to the storage root.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        ...

    def save_metadata(self, metadata: DocumentMetadata) -> None:
        """Persist document metadata keyed by document identifier."""
        ...

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        """Load persisted metadata for a document.

        Raises:
            FileNotFoundError: If metadata for the document does not exist.
        """
        ...
