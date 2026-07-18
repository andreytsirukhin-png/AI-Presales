from pydantic import BaseModel, Field


class IndexedChunk(BaseModel):
    """A stored embedding vector for a document chunk."""

    index: int = Field(..., ge=0, description="Zero-based chunk index.")
    vector: list[float] = Field(..., description="Stored embedding vector for the chunk.")


class IndexResponse(BaseModel):
    """API response returned after indexing document embeddings."""

    document_id: str = Field(..., description="Identifier of the indexed document.")
    chunks_indexed: int = Field(..., ge=0, description="Number of chunks stored in the vector store.")
    status: str = Field(..., description="Indexing lifecycle status.")
