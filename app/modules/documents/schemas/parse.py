from pydantic import BaseModel, Field


class ParsedPdf(BaseModel):
    """Structured result produced by the PDF parser."""

    page_count: int = Field(..., ge=0, description="Number of pages in the PDF.")
    text: str = Field(..., description="Extracted plain text from all pages.")


class ParseResponse(BaseModel):
    """API response returned after a successful document parse."""

    document_id: str = Field(..., description="Identifier of the parsed document.")
    page_count: int = Field(..., ge=0, description="Number of pages in the PDF.")
    text: str = Field(..., description="Extracted plain text from all pages.")
    status: str = Field(..., description="Parse lifecycle status.")
