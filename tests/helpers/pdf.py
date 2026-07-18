"""Helpers for building valid minimal PDF fixtures used in tests."""


def make_text_pdf(text: str) -> bytes:
    """Build a minimal one-page PDF that contains the given text.

    The generated PDF includes a correct xref table and startxref offset so
    it can be opened with ``PdfReader(..., strict=True)``.

    Args:
        text: Plain text to embed in the page content stream.

    Returns:
        Raw PDF bytes.
    """
    escaped = (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped}) Tj ET".encode("latin-1", "replace")

    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        (
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
        ),
        (
            f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        ),
        b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n",
    ]

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray()
    offsets = [0]
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        body.extend(obj)
        cursor += len(obj)

    xref_offset = cursor
    xref = bytearray()
    xref.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    xref.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        xref.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return bytes(header) + bytes(body) + bytes(xref) + trailer


def make_empty_pdf() -> bytes:
    """Build a valid one-page PDF with no extractable text content."""
    stream = b"BT ET"
    objects = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n",
        (
            b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R >>endobj\n"
        ),
        (
            f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
            + stream
            + b"\nendstream\nendobj\n"
        ),
    ]

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray()
    offsets = [0]
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        body.extend(obj)
        cursor += len(obj)

    xref_offset = cursor
    xref = bytearray()
    xref.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    xref.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        xref.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    trailer = (
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")

    return bytes(header) + bytes(body) + bytes(xref) + trailer
