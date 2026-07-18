from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.storage.protocol import FileStorage
from app.modules.documents.parsers.pdf_parser import PDFParser
from app.modules.documents.schemas.parse import ParseResponse

PDF_EXTENSION = ".pdf"


class ParseService:
    """Orchestrates loading stored documents and extracting their text."""

    def __init__(
        self,
        storage: FileStorage,
        parser: PDFParser | None = None,
    ) -> None:
        self._storage = storage
        self._parser = parser or PDFParser()

    def parse(self, document_id: str) -> ParseResponse:
        """Load a stored PDF and extract its text content.

        Args:
            document_id: Identifier returned by the upload endpoint.

        Returns:
            Parsed document metadata and extracted text.

        Raises:
            DocumentNotFoundError: If the document or its metadata does not exist.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        storage_path = f"{document_id}{PDF_EXTENSION}"

        try:
            metadata = self._storage.get_metadata(document_id)
        except FileNotFoundError as exc:
            raise DocumentNotFoundError(
                f"Document not found: {document_id}"
            ) from exc

        try:
            content = self._storage.load(storage_path)
        except FileNotFoundError as exc:
            raise DocumentNotFoundError(
                f"Document not found: {document_id}"
            ) from exc

        parsed = self._parser.parse(content)

        self._storage.save_metadata(
            metadata.model_copy(
                update={
                    "status": "parsed",
                    "page_count": parsed.page_count,
                    "characters": parsed.characters,
                }
            )
        )

        return ParseResponse(
            document_id=document_id,
            page_count=parsed.page_count,
            pages=parsed.pages,
            characters=parsed.characters,
            text=parsed.text,
            status="parsed",
        )
