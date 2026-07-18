from io import BytesIO

import pytest
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, NumberObject, StreamObject


def make_blank_pdf(page_count: int = 1) -> bytes:
    """Build a valid PDF with blank pages and no extractable text."""
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_text_pdf(text: str = "Hello World") -> bytes:
    """Return a valid one-page PDF containing the given extractable text."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_bytes = f"BT /F1 12 Tf 100 700 Td ({escaped}) Tj ET".encode("latin-1")

    content_stream = StreamObject()
    content_stream._data = content_bytes
    content_stream[NameObject("/Length")] = NumberObject(len(content_bytes))
    page[NameObject("/Contents")] = content_stream

    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    resources = page.get("/Resources") or DictionaryObject()
    fonts = resources.get("/Font") or DictionaryObject()
    fonts[NameObject("/F1")] = font
    resources[NameObject("/Font")] = fonts
    page[NameObject("/Resources")] = resources

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def text_pdf() -> bytes:
    return make_text_pdf()


@pytest.fixture
def blank_pdf() -> bytes:
    return make_blank_pdf()
