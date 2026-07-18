from datetime import UTC, datetime

import pytest

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.chunk_service import ChunkService
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


class FakeFileStorage:
    """In-memory storage adapter used by chunk-service unit tests."""

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


def _seed_uploaded_metadata(
    storage: FakeFileStorage,
    document_id: str,
    *,
    size_bytes: int = 128,
) -> None:
    storage.save_metadata(
        DocumentMetadata(
            document_id=document_id,
            filename=f"{document_id}.pdf",
            content_type="application/pdf",
            size_bytes=size_bytes,
            status="uploaded",
            page_count=None,
            characters=None,
            created_at=datetime.now(UTC),
        )
    )


@pytest.fixture
def storage() -> FakeFileStorage:
    return FakeFileStorage()


@pytest.fixture
def chunk_service(storage: FakeFileStorage) -> ChunkService:
    return ChunkService(storage)


def test_chunk_returns_expected_response(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "doc-123"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Requirement one for chunking")
    _seed_uploaded_metadata(storage, document_id)

    result = chunk_service.chunk(document_id)

    assert result.document_id == document_id
    assert result.chunk_count == len(result.chunks)
    assert result.chunk_count >= 1
    assert "Requirement one" in result.chunks[0].text


def test_chunk_raises_when_metadata_missing(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "orphan-doc"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Orphan file")

    with pytest.raises(DocumentNotFoundError):
        chunk_service.chunk(document_id)


def test_chunk_raises_when_pdf_missing(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "missing-pdf"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(DocumentNotFoundError):
        chunk_service.chunk(document_id)


def test_chunk_raises_for_invalid_pdf(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc"
    storage.files[f"{document_id}.pdf"] = b"%PDF-1.4 corrupted content"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(InvalidPdfError):
        chunk_service.chunk(document_id)


def test_chunk_raises_for_empty_pdf(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc"
    storage.files[f"{document_id}.pdf"] = make_blank_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        chunk_service.chunk(document_id)


def test_chunk_raises_for_empty_pdf_helper(
    chunk_service: ChunkService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc-2"
    storage.files[f"{document_id}.pdf"] = make_empty_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        chunk_service.chunk(document_id)
