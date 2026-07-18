from pydantic import BaseModel, Field


class Embedding(BaseModel):
    """Vector representation of a single text chunk."""

    index: int = Field(..., ge=0, description="Zero-based chunk index.")
    text: str = Field(..., description="Source text for the chunk.")
    vector: list[float] = Field(..., description="Embedding vector for the chunk text.")


class EmbeddingResponse(BaseModel):
    """API response returned after generating document embeddings."""

    document_id: str = Field(..., description="Identifier of the embedded document.")
    chunk_count: int = Field(..., ge=0, description="Number of embedded chunks.")
    embedding_dimension: int = Field(..., gt=0, description="Size of each embedding vector.")
    status: str = Field(..., description="Embedding lifecycle status.")
