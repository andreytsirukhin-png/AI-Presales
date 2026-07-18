from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.storage.protocol import FileStorage
from app.modules.documents.parsers.pdf_parser import PDFParser
from app.modules.documents.schemas.parse import ParseResponse


class ParseService:
    """Loads a stored PDF and extracts its text content."""

    def __init__(
        self,
        storage: FileStorage,
        parser: PDFParser | None = None,
    ) -> None:
        self._storage = storage
        self._parser = parser or PDFParser()

    def parse(self, document_id: str) -> ParseResponse:
        """Parse a previously uploaded PDF document.

        Args:
            document_id: Identifier returned by the upload service.

        Returns:
            Extracted text and page metadata for the document.

        Raises:
            DocumentNotFoundError: If no stored file exists for the document.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        storage_path = f"{document_id}.pdf"
        try:
            content = self._storage.load(storage_path)
        except FileNotFoundError as exc:
            raise DocumentNotFoundError(
                f"Document '{document_id}' was not found."
            ) from exc

        parsed = self._parser.parse(content)
        return ParseResponse(
            document_id=document_id,
            page_count=parsed.page_count,
            text=parsed.text,
            status="parsed",
        )
