from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.infrastructure.storage.local_storage import LocalFileStorage
from app.modules.documents.schemas.document import DocumentMetadata


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(root_dir=tmp_path)


def test_save_and_get_metadata(storage: LocalFileStorage) -> None:
    metadata = DocumentMetadata(
        document_id="doc-123",
        filename="proposal.pdf",
        content_type="application/pdf",
        size_bytes=2048,
        status="uploaded",
        page_count=None,
        characters=None,
        created_at=datetime.now(UTC),
    )

    storage.save_metadata(metadata)

    loaded = storage.get_metadata("doc-123")
    assert loaded == metadata


def test_get_metadata_raises_when_missing(storage: LocalFileStorage) -> None:
    with pytest.raises(FileNotFoundError):
        storage.get_metadata("missing-doc")
