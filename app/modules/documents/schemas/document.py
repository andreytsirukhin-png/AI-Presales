from pydantic import BaseModel, Field


class ParseResponse(BaseModel):
    """Response returned after successfully parsing a document."""

    document_id: str = Field(..., description="Unique identifier for the parsed document.")
    pages: int = Field(..., description="Number of pages in the PDF.")
    characters: int = Field(..., description="Number of characters in the extracted text.")
    text: str = Field(..., description="Text extracted from the PDF.")
