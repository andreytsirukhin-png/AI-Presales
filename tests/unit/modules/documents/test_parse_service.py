import pytest

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.modules.documents.services.parse_service import ParseService
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


class FakeFileStorage:
    """In-memory storage adapter used by parse-service unit tests."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    def save(self, relative_path: str, content: bytes) -> None:
        self.files[relative_path] = content

    def load(self, relative_path: str) -> bytes:
        try:
            return self.files[relative_path]
        except KeyError as exc:
            raise FileNotFoundError(relative_path) from exc


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

    result = parse_service.parse(document_id)

    assert result.document_id == document_id
    assert result.status == "parsed"
    assert result.page_count == 1
    assert result.pages == 1
    assert "Requirement one" in result.text
    assert result.characters == len(result.text)


def test_parse_raises_when_document_missing(parse_service: ParseService) -> None:
    with pytest.raises(DocumentNotFoundError):
        parse_service.parse("missing-doc")


def test_parse_raises_for_invalid_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc"
    storage.files[f"{document_id}.pdf"] = b"%PDF-1.4 corrupted content"

    with pytest.raises(InvalidPdfError):
        parse_service.parse(document_id)


def test_parse_propagates_invalid_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "bad-doc-2"
    storage.files[f"{document_id}.pdf"] = b"%PDF-not-really"

    with pytest.raises(InvalidPdfError):
        parse_service.parse(document_id)


def test_parse_raises_for_empty_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc"
    storage.files[f"{document_id}.pdf"] = make_blank_pdf()

    with pytest.raises(EmptyPdfError):
        parse_service.parse(document_id)


def test_parse_propagates_empty_pdf(
    parse_service: ParseService,
    storage: FakeFileStorage,
) -> None:
    document_id = "empty-doc-2"
    storage.files[f"{document_id}.pdf"] = make_empty_pdf()

    with pytest.raises(EmptyPdfError):
        parse_service.parse(document_id)
