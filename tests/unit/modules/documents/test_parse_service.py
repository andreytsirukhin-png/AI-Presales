import pytest

from datetime import UTC, datetime

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.services.parse_service import ParseService
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


class FakeFileStorage:
    """In-memory storage adapter used by parse-service unit tests."""

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
def parse_service(storage: FakeFileStorage) -> ParseService:
    return ParseService(storage)


def test_parse_returns_expected_response(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "doc-123"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Requirement one")
    _seed_uploaded_metadata(storage, document_id)

    result = parse_service.parse(document_id)

    assert result.document_id == document_id
    assert result.status == "parsed"
    assert result.page_count == 1
    assert result.pages == 1
    assert "Requirement one" in result.text
    assert result.characters == len(result.text)
    updated_metadata = storage.metadata[document_id]
    assert updated_metadata.status == "parsed"
    assert updated_metadata.page_count == 1
    assert updated_metadata.characters == result.characters


def test_parse_raises_when_document_missing(parse_service: ParseService) -> None:
    with pytest.raises(DocumentNotFoundError):
        parse_service.parse("missing-doc")


def test_parse_raises_when_metadata_missing(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "orphan-doc"
    storage.files[f"{document_id}.pdf"] = make_text_pdf("Orphan file")

    with pytest.raises(DocumentNotFoundError):
        parse_service.parse(document_id)


def test_parse_raises_for_invalid_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc"
    storage.files[f"{document_id}.pdf"] = b"%PDF-1.4 corrupted content"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(InvalidPdfError):
        parse_service.parse(document_id)


def test_parse_propagates_invalid_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc-2"
    storage.files[f"{document_id}.pdf"] = b"%PDF-not-really"
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(InvalidPdfError):
        parse_service.parse(document_id)


def test_parse_raises_for_empty_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc"
    storage.files[f"{document_id}.pdf"] = make_blank_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        parse_service.parse(document_id)


def test_parse_propagates_empty_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc-2"
    storage.files[f"{document_id}.pdf"] = make_empty_pdf()
    _seed_uploaded_metadata(storage, document_id)

    with pytest.raises(EmptyPdfError):
        parse_service.parse(document_id)
