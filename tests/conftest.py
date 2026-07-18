from io import BytesIO

import pytest
from pypdf import PdfWriter

TEXT_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Hello World) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000368 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
465
%%EOF"""


def make_blank_pdf(page_count: int = 1) -> bytes:
    """Build a valid PDF with blank pages and no extractable text."""
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_text_pdf(text: str = "Hello World") -> bytes:
    """Return a minimal valid PDF containing the given text."""
    if text == "Hello World":
        return TEXT_PDF

    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 100 700 Td ({escaped}) Tj ET"
    content_bytes = content.encode("latin-1")
    length = len(content_bytes)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        + f"4 0 obj<</Length {length}>>stream\n".encode()
        + content_bytes
        + b"\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"trailer<</Size 6/Root 1 0 R>>\n"
        b"startxref\n0\n"
        b"%%EOF"
    )


@pytest.fixture
def text_pdf() -> bytes:
    return make_text_pdf()


@pytest.fixture
def blank_pdf() -> bytes:
    return make_blank_pdf()
