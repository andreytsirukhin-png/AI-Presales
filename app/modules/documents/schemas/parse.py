from pydantic import BaseModel, Field


class ParsedPdf(BaseModel):
    """Structured result produced by the PDF parser."""

    page_count: int = Field(..., ge=0, description="Number of pages in the PDF.")
    text: str = Field(..., description="Extracted plain text from all pages.")

    @property
    def pages(self) -> int:
        """Alias for page count used by US-002 consumers."""
        return self.page_count

    @property
    def characters(self) -> int:
        """Number of characters in the extracted text."""
        return len(self.text)


class ParseResponse(BaseModel):
    """API response returned after a successful document parse."""

    document_id: str = Field(..., description="Identifier of the parsed document.")
    page_count: int = Field(..., ge=0, description="Number of pages in the PDF.")
    pages: int = Field(..., ge=0, description="Number of pages in the PDF.")
    characters: int = Field(..., ge=0, description="Number of characters in extracted text.")
    text: str = Field(..., description="Extracted plain text from all pages.")
    status: str = Field(..., description="Parse lifecycle status.")
