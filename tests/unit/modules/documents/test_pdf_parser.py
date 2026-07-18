import pytest

from app.core.exceptions import EmptyPdfError, InvalidPdfError
from app.modules.documents.parsers.pdf_parser import PDFParser
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf


@pytest.fixture
def parser() -> PDFParser:
    return PDFParser()


def test_parse_extracts_text_and_metadata(parser: PDFParser) -> None:
    content = make_text_pdf("Sample RFP content")

    result = parser.parse(content)

    assert result.page_count == 1
    assert result.pages == 1
    assert "Sample RFP content" in result.text
    assert result.characters == len(result.text)


def test_parse_rejects_invalid_pdf(parser: PDFParser) -> None:
    with pytest.raises(InvalidPdfError):
        parser.parse(b"%PDF-1.4 this is not a valid pdf structure")


def test_parse_rejects_non_pdf_bytes(parser: PDFParser) -> None:
    with pytest.raises(InvalidPdfError):
        parser.parse(b"not a pdf")


def test_parse_rejects_empty_pdf(parser: PDFParser) -> None:
    with pytest.raises(EmptyPdfError):
        parser.parse(make_blank_pdf())


def test_parse_counts_multiple_pages(parser: PDFParser) -> None:
    content = make_blank_pdf(page_count=3)

    with pytest.raises(EmptyPdfError):
        parser.parse(content)


def test_parse_rejects_whitespace_only_pdf(parser: PDFParser) -> None:
    with pytest.raises(EmptyPdfError):
        parser.parse(make_text_pdf("   \n\t  "))
