from datetime import UTC, datetime

import pytest

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.infrastructure.embeddings.mock_provider import MOCK_EMBEDDING_DIMENSION, MockEmbeddingProvider
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.metadata_service import MetadataService
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


class FakeFileStorage:
    """In-memory storage adapter used by embedding-service unit tests."""

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


class RecordingEmbeddingProvider:
    """Test double that records embedding calls."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def dimension(self) -> int:
        return MOCK_EMBEDDING_DIMENSION

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return MockEmbeddingProvider().embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self.calls.extend(texts)
        return [MockEmbeddingProvider().embed(text) for text in texts]


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
def provider() -> RecordingEmbeddingProvider:
    return RecordingEmbeddingProvider()


@pytest.fixture
def embedding_service(
    storage: FakeFileStorage,
    provider: RecordingEmbeddingProvider,
) -> EmbeddingService:
    metadata_service = MetadataService(storage)
    chunk_service = ChunkService(storage)
    return EmbeddingService(
        metadata_service=metadata_service,
        chunk_service=chunk_service,
        provider=provider,
        embedding_model="mock",
    )


def test_embed_returns_expected_response(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
    provider: RecordingEmbeddingProvider,
) -> None:
    document_id = "doc-123"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Requirement one for embeddings")
    _seed_uploaded_metadata(storage, document_id)

    result = embedding_service.embed(document_id)

    assert result.document_id == document_id
    assert result.status == "embedded"
    assert result.embedding_dimension == MOCK_EMBEDDING_DIMENSION
    assert result.chunk_count == len(provider.calls)
    assert result.chunk_count >= 1


def test_embed_raises_when_metadata_missing(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
) -> None:
    document_id = "orphan-doc"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Orphan file")

    with pytest.raises(DocumentNotFoundError):
        embedding_service.embed(document_id)


def test_embed_raises_when_pdf_missing(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
) -> None:
    document_id = "missing-pdf"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(DocumentNotFoundError):
        embedding_service.embed(document_id)


def test_embed_raises_for_invalid_pdf(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc"
    storage.files[f"{document_id}.pdf"] = b"%PDF-1.4 corrupted content"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(InvalidPdfError):
        embedding_service.embed(document_id)


def test_embed_raises_for_empty_pdf(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc"
    storage.files[f"{document_id}.pdf"] = make_blank_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        embedding_service.embed(document_id)


def test_embed_raises_for_empty_pdf_helper(
    embedding_service: EmbeddingService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc-2"
    storage.files[f"{document_id}.pdf"] = make_empty_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        embedding_service.embed(document_id)
