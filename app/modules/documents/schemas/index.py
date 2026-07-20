from pydantic import BaseModel, Field

from app.modules.documents.schemas.source_metadata import SourceMetadata


class IndexedChunk(BaseModel):
    """A stored embedding vector for a document chunk."""

    index: int = Field(..., ge=0, description="Zero-based chunk index.")
    text: str = Field(..., description="Source text for the chunk.")
    vector: list[float] = Field(..., description="Stored embedding vector for the chunk.")
    metadata: SourceMetadata | None = Field(
        default=None,
        description="Traceability metadata persisted with the chunk.",
    )


class IndexResponse(BaseModel):
    """API response returned after indexing document embeddings."""

    document_id: str = Field(..., description="Identifier of the indexed document.")
    chunks_indexed: int = Field(..., ge=0, description="Number of chunks stored in the vector store.")
    status: str = Field(..., description="Indexing lifecycle status.")
