from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.storage.protocol import FileStorage
from app.modules.documents.chunkers.text_chunker import TextChunker
from app.modules.documents.parsers.pdf_parser import PDFParser
from app.modules.documents.schemas.chunk import ChunkResponse

PDF_EXTENSION = ".pdf"


class ChunkService:
    """Loads, parses, and chunks stored PDF documents."""

    def __init__(
        self,
        storage: FileStorage,
        parser: PDFParser | None = None,
        chunker: TextChunker | None = None,
    ) -> None:
        self._storage = storage
        self._parser = parser or PDFParser()
        self._chunker = chunker or TextChunker()

    def chunk(self, document_id: str) -> ChunkResponse:
        """Parse a stored PDF and split its text into chunks.

        Args:
            document_id: Identifier returned by the upload endpoint.

        Returns:
            Ordered text chunks for the document.

        Raises:
            DocumentNotFoundError: If the document or its metadata does not exist.
            InvalidPdfError: If the stored file is not a readable PDF.
            EmptyPdfError: If the PDF contains no extractable text.
        """
        storage_path = f"{document_id}{PDF_EXTENSION}"

        try:
            self._storage.get_metadata(document_id)
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
        if parsed.page_texts:
            chunks = self._chunker.chunk_with_pages(parsed.text, parsed.page_texts)
        else:
            chunks = self._chunker.chunk(parsed.text)

        return ChunkResponse(
            document_id=document_id,
            chunk_count=len(chunks),
            chunks=chunks,
        )
