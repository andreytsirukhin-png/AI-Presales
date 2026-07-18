"""Helpers for building valid minimal PDF fixtures used in tests."""

from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def make_text_pdf(text: str) -> bytes:
    """Build a one-page PDF containing the given extractable text.

    Uses ``pypdf.PdfWriter`` so the xref table and ``startxref`` offset are
    produced by the library rather than hand-calculated.

    Args:
        text: Plain text to embed in the page content stream.

    Returns:
        Raw PDF bytes readable with ``PdfReader(..., strict=True)``.
    """
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    escaped = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    content = DecodedStreamObject()
    content.set_data(
        f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1", "replace")
    )
    page.replace_contents(content)
    page[NameObject("/Resources")] = DictionaryObject(
        {
            NameObject("/Font"): DictionaryObject(
                {
                    NameObject("/F1"): DictionaryObject(
                        {
                            NameObject("/Type"): NameObject("/Font"),
                            NameObject("/Subtype"): NameObject("/Type1"),
                            NameObject("/BaseFont"): NameObject("/Helvetica"),
                        }
                    ),
                }
            ),
        }
    )

    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def make_empty_pdf() -> bytes:
    """Build a valid one-page PDF with no extractable text content."""
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
