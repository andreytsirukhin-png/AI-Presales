from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request payload for semantic document search."""

    query: str = Field(..., min_length=1, description="Natural-language search query.")
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of ranked chunks to return.",
    )


class SearchResult(BaseModel):
    """A ranked chunk match for a search query."""

    chunk_index: int = Field(..., ge=0, description="Zero-based index of the matched chunk.")
    text: str = Field(..., description="Text content of the matched chunk.")
    score: float = Field(..., description="Cosine similarity score for the match.")


class SearchResponse(BaseModel):
    """API response returned after searching an indexed document."""

    document_id: str = Field(..., description="Identifier of the searched document.")
    query: str = Field(..., description="Query string used for the search.")
    result_count: int = Field(..., ge=0, description="Number of returned search results.")
    results: list[SearchResult] = Field(..., description="Ranked chunk matches.")
