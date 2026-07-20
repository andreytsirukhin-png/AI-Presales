from datetime import UTC, datetime

import pytest

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from app.infrastructure.vector_store.in_memory_store import InMemoryVectorStore
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


class FakeFileStorage:
    """In-memory storage adapter used by index-service unit tests."""

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
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def index_service(
    storage: FakeFileStorage,
    vector_store: InMemoryVectorStore,
) -> IndexService:
    metadata_service = MetadataService(storage)
    chunk_service = ChunkService(storage)
    embedding_service = EmbeddingService(
        metadata_service=metadata_service,
        chunk_service=chunk_service,
        provider=MockEmbeddingProvider(),
        embedding_model="mock",
    )
    return IndexService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def test_index_returns_expected_response_and_stores_embeddings(
    index_service: IndexService,
    storage: FakeFileStorage,
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-123"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Requirement one for indexing")
    _seed_uploaded_metadata(storage, document_id)

    result = index_service.index(document_id)
    stored = vector_store.get(document_id)

    assert result.document_id == document_id
    assert result.status == "indexed"
    assert result.chunks_indexed >= 1
    assert len(stored) == result.chunks_indexed
    assert stored[0].metadata is not None
    assert stored[0].metadata.document_name == f"{document_id}.pdf"
    assert stored[0].metadata.embedding_model == "mock"


def test_index_raises_when_metadata_missing(
    index_service: IndexService,
    storage: FakeFileStorage,
) -> None:
    document_id = "orphan-doc"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Orphan file")

    with pytest.raises(DocumentNotFoundError):
        index_service.index(document_id)


def test_index_raises_when_pdf_missing(
    index_service: IndexService,
    storage: FakeFileStorage,
) -> None:
    document_id = "missing-pdf"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(DocumentNotFoundError):
        index_service.index(document_id)


def test_index_raises_for_invalid_pdf(
    index_service: IndexService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc"
    storage.files[f"{document_id}.pdf"] = b"%PDF-1.4 corrupted content"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(InvalidPdfError):
        index_service.index(document_id)


def test_index_raises_for_empty_pdf(
    index_service: IndexService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc"
    storage.files[f"{document_id}.pdf"] = make_blank_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        index_service.index(document_id)


def test_index_raises_for_empty_pdf_helper(
    index_service: IndexService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc-2"
    storage.files[f"{document_id}.pdf"] = make_empty_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        index_service.index(document_id)
