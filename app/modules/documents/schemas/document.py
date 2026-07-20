from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.documents.schemas.parse import ParseResponse

DocumentStatus = Literal["uploaded", "parsed", "failed"]


class DocumentMetadata(BaseModel):
    """Stored metadata for an uploaded document."""

    document_id: str = Field(..., description="Unique identifier for the document.")
    filename: str = Field(..., description="Original filename supplied by the client.")
    content_type: str = Field(..., description="MIME type reported during upload.")
    size_bytes: int = Field(..., ge=0, description="Size of the uploaded file in bytes.")
    status: DocumentStatus = Field(..., description="Document lifecycle status.")
    page_count: int | None = Field(
        default=None,
        ge=0,
        description="Number of pages after parsing.",
    )
    characters: int | None = Field(
        default=None,
        ge=0,
        description="Number of extracted characters after parsing.",
    )
    created_at: datetime = Field(..., description="UTC timestamp when the document was uploaded.")
    project_id: str | None = Field(
        default=None,
        description="Owning project identifier when uploaded via a workspace.",
    )
    chunks_indexed: int | None = Field(
        default=None,
        ge=0,
        description="Number of chunks indexed for this document.",
    )
    indexed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp when the document was last indexed.",
    )


__all__ = ["DocumentMetadata", "DocumentStatus", "ParseResponse"]
