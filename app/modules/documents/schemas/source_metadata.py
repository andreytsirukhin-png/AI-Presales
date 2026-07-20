from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    """Traceability metadata for an indexed document chunk."""

    document_id: str = Field(..., description="Unique document identifier.")
    document_name: str = Field(..., description="Original uploaded filename.")
    page_number: int | None = Field(
        default=None,
        ge=1,
        description="One-based PDF page number when available.",
    )
    chunk_id: str = Field(..., description="Stable chunk identifier within the document.")
    chunk_index: int = Field(..., ge=0, description="Zero-based chunk index.")
    embedding_model: str = Field(..., description="Embedding model used to index the chunk.")
    created_at: str = Field(..., description="UTC timestamp when the chunk was indexed.")
    section: str | None = Field(default=None, description="Optional document section label.")
    heading: str | None = Field(default=None, description="Optional heading near the chunk.")


def build_chunk_id(document_id: str, chunk_index: int) -> str:
    """Return a stable chunk identifier for storage and citations."""
    return f"{document_id}-chunk-{chunk_index}"
