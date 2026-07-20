from pydantic import BaseModel, Field


class TextChunk(BaseModel):
    """A contiguous slice of parsed document text."""

    index: int = Field(..., ge=0, description="Zero-based position in the chunk sequence.")
    text: str = Field(..., description="Chunk text with leading and trailing whitespace removed.")
    characters: int = Field(..., ge=0, description="Number of characters in the chunk text.")
    page_number: int | None = Field(
        default=None,
        ge=1,
        description="One-based PDF page number when available.",
    )
    section: str | None = Field(default=None, description="Optional section label.")
    heading: str | None = Field(default=None, description="Optional heading near the chunk.")


class ChunkResponse(BaseModel):
    """API response returned after chunking a parsed document."""

    document_id: str = Field(..., description="Identifier of the chunked document.")
    chunk_count: int = Field(..., ge=0, description="Number of returned chunks.")
    chunks: list[TextChunk] = Field(..., description="Ordered text chunks for the document.")
