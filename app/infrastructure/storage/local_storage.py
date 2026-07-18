from pathlib import Path

from app.modules.documents.schemas.document import DocumentMetadata


class LocalFileStorage:
    """Stores files and metadata on the local filesystem under a configurable root."""

    def __init__(self, root_dir: Path | str = "uploads") -> None:
        self._root_dir = Path(root_dir)

    def save(self, relative_path: str, content: bytes) -> None:
        """Write content to disk, creating parent directories as needed."""
        destination = self._root_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def load(self, relative_path: str) -> bytes:
        """Read content from disk.

        Raises:
            FileNotFoundError: If the relative path does not exist.
        """
        source = self._root_dir / relative_path
        if not source.is_file():
            raise FileNotFoundError(relative_path)
        return source.read_bytes()

    def save_metadata(self, metadata: DocumentMetadata) -> None:
        """Write document metadata as JSON alongside stored files."""
        destination = self._metadata_path(metadata.document_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(metadata.model_dump_json(), encoding="utf-8")

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        """Read persisted document metadata from disk.

        Raises:
            FileNotFoundError: If metadata for the document does not exist.
        """
        source = self._metadata_path(document_id)
        if not source.is_file():
            raise FileNotFoundError(document_id)
        return DocumentMetadata.model_validate_json(source.read_text(encoding="utf-8"))

    def _metadata_path(self, document_id: str) -> Path:
        """Return the filesystem path for a document's metadata file."""
        return self._root_dir / f"{document_id}.meta.json"
