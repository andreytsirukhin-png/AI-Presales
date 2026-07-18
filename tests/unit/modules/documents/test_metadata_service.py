from datetime import UTC, datetime

import pytest

from app.core.exceptions import DocumentNotFoundError
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.metadata_service import MetadataService


class FakeFileStorage:
    """In-memory storage adapter used by metadata-service unit tests."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.metadata: dict[str, DocumentMetadata] = {}

    def save(self, relative_path: str, content: bytes) -> None:
        self.files[relative_path] = content

    def load(self, relative_path: str) -> bytes:
        try:
            return self.files[relative_path]
        except KeyError as exc:
            raise FileNotFoundError(relative_path) from exc

    def save_metadata(self, metadata: DocumentMetadata) -> None:
        self.metadata[metadata.document_id] = metadata

    def get_metadata(self, document_id: str) -> DocumentMetadata:
        try:
            return self.metadata[document_id]
        except KeyError as exc:
            raise FileNotFoundError(document_id) from exc


@pytest.fixture
def storage() -> FakeFileStorage:
    return FakeFileStorage()


@pytest.fixture
def metadata_service(storage: FakeFileStorage) -> MetadataService:
    return MetadataService(storage)


def test_get_returns_persisted_metadata(
    metadata_service: MetadataService,
    storage: FakeFileStorage,
) -> None:
    metadata = DocumentMetadata(
        document_id="doc-123",
        filename="proposal.pdf",
        content_type="application/pdf",
        size_bytes=1024,
        status="uploaded",
        page_count=None,
        characters=None,
        created_at=datetime.now(UTC),
    )
    storage.save_metadata(metadata)

    result = metadata_service.get("doc-123")

    assert result == metadata


def test_get_raises_when_metadata_missing(metadata_service: MetadataService) -> None:
    with pytest.raises(DocumentNotFoundError):
        metadata_service.get("missing-doc")
