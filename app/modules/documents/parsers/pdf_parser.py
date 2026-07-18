from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.exceptions import EmptyPdfError, InvalidPdfError
from app.modules.documents.schemas.parse import ParsedPdf


class PDFParser:
    """Extracts text content from PDF byte streams."""

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
        except Exception as exc:
            raise InvalidPdfError("Unable to read PDF file.") from exc

        if reader.is_encrypted:
            try:
                if reader.decrypt("") == 0:
                    raise InvalidPdfError("Unable to read encrypted PDF file.")
            except PdfReadError as exc:
                raise InvalidPdfError("Unable to read encrypted PDF file.") from exc

        page_count = len(reader.pages)
        if page_count == 0:
            raise EmptyPdfError("PDF contains no pages.")

        extracted_pages: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            extracted_pages.append(page_text)

        text = "\n".join(extracted_pages).strip()
        if not text:
            raise EmptyPdfError("PDF contains no extractable text.")

        return ParsedPdf(page_count=page_count, text=text)
