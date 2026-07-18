from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import EmptyPdfError, InvalidPdfError
from app.modules.documents.schemas.parse import ParsedPdf


class PDFParser:
    """Extracts plain text and page metadata from PDF bytes."""

    def parse(self, content: bytes) -> ParsedPdf:
        """Parse PDF bytes and return extracted text with metadata.

        Args:
            content: Raw PDF file bytes.

        Returns:
            Parsed PDF metadata including page count and extracted text.

        Raises:
            InvalidPdfError: If the bytes are not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        try:
            reader = PdfReader(BytesIO(content), strict=True)
        except PdfReadError as exc:
            raise InvalidPdfError("Unable to read PDF file.") from exc

        page_texts: list[str] = []
        for page in reader.pages:
            extracted = page.extract_text() or ""
            page_texts.append(extracted)

        text = "\n".join(page_texts).strip()
        if not text:
            raise EmptyPdfError("PDF contains no extractable text.")

        return ParsedPdf(page_count=len(reader.pages), text=text)
