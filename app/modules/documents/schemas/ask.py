from pydantic import BaseModel, Field

from app.modules.documents.schemas.source_metadata import SourceMetadata


class AnswerCitation(BaseModel):
    """Compact citation reference for a generated answer."""

    document: str = Field(..., description="Source document filename.")
    page: int | None = Field(default=None, ge=1, description="One-based page number when known.")
    score: float = Field(..., description="Retrieval similarity score.")
    chunk_index: int | None = Field(default=None, ge=0, description="Zero-based chunk index.")
    chunk_id: str | None = Field(default=None, description="Stable chunk identifier.")


class AskRequest(BaseModel):
    """Request payload for document question answering."""

    question: str = Field(..., min_length=1, description="Natural-language question.")
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of context chunks to retrieve.",
    )


class AnswerSource(BaseModel):
    """A retrieved chunk used to ground an answer."""

    chunk_index: int = Field(..., ge=0, description="Zero-based index of the source chunk.")
    text: str = Field(..., description="Text content of the source chunk.")
    score: float = Field(..., description="Semantic similarity score for the source chunk.")
    metadata: SourceMetadata | None = Field(
        default=None,
        description="Traceability metadata for the source chunk.",
    )


class AskResponse(BaseModel):
    """API response returned after answering a document question."""

    document_id: str = Field(..., description="Identifier of the queried document.")
    question: str = Field(..., description="Question submitted by the client.")
    answer: str = Field(..., description="Generated answer grounded in retrieved sources.")
    sources: list[AnswerSource] = Field(..., description="Retrieved chunks used as answer context.")
    citations: list[AnswerCitation] = Field(
        default_factory=list,
        description="Compact citation list derived from retrieved sources.",
    )
    status: str = Field(..., description="Question answering lifecycle status.")
