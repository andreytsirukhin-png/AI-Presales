from pydantic import BaseModel, Field

from app.modules.documents.schemas.ask import AnswerCitation, AnswerSource
from app.modules.documents.schemas.search import SearchRequest, SearchResult


class ProjectSearchResponse(BaseModel):
    """Semantic search results scoped to one project."""

    project_id: str
    query: str
    result_count: int = Field(..., ge=0)
    results: list[SearchResult]


class ProjectAskRequest(BaseModel):
    """Question-answering request scoped to a project."""

    question: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


class ProjectAskResponse(BaseModel):
    """Answer grounded in project-wide retrieved context."""

    project_id: str
    question: str
    answer: str
    sources: list[AnswerSource]
    citations: list[AnswerCitation] = Field(default_factory=list)
    status: str
