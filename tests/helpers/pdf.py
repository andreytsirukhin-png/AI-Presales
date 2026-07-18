"""Helpers for building valid minimal PDF fixtures used in tests."""


def _build_pdf(objects: list[bytes]) -> bytes:
    """Assemble a minimal PDF with a correct xref table and startxref.

    Offset calculation:
    1. Write the header; ``cursor`` starts at ``len(header)``.
    2. For each object body, record ``cursor`` as that object's byte offset,
       then advance ``cursor`` by ``len(object)``.
    3. After all objects, ``cursor`` is the byte offset of the ``xref`` keyword.
    4. Emit xref rows: object 0 as free, objects 1..N as ``n`` with the
       recorded offsets (10-digit, zero-padded).
    5. Emit trailer with ``startxref`` equal to the xref keyword offset.
    """
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    # offsets[0] is unused (free object); offsets[i] is the file offset of object i.
    offsets = [0]
    body = bytearray()
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        body.extend(obj)
        cursor += len(obj)

    xref_offset = cursor  # byte offset of the "xref" keyword that follows

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
    return _build_pdf(objects)


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
    return _build_pdf(objects)
