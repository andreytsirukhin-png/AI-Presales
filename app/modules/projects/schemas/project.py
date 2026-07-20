from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request payload for creating a workspace project."""

    project_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class ProjectMetadata(BaseModel):
    """Persisted metadata for a multi-document workspace project."""

    project_id: str = Field(..., description="Unique project identifier.")
    project_name: str = Field(..., description="Human-readable project name.")
    description: str = Field(default="", description="Optional project description.")
    created_at: datetime = Field(..., description="UTC timestamp when the project was created.")
    document_ids: list[str] = Field(
        default_factory=list,
        description="Document identifiers belonging to this project.",
    )
    last_indexed_at: datetime | None = Field(
        default=None,
        description="UTC timestamp of the most recent successful document indexing.",
    )


class ProjectResponse(BaseModel):
    """API representation of a project."""

    project_id: str
    project_name: str
    description: str
    created_at: datetime
    document_count: int = Field(..., ge=0)
    last_indexed_at: datetime | None = None


class ProjectListResponse(BaseModel):
    """API response listing workspace projects."""

    projects: list[ProjectResponse]
    count: int = Field(..., ge=0)


class ProjectStatisticsResponse(BaseModel):
    """Runtime statistics for a project workspace."""

    project_id: str
    project_name: str
    document_count: int = Field(..., ge=0)
    indexed_chunks: int = Field(..., ge=0)
    embedding_provider: str
    embedding_model: str
    vector_store: str
    last_indexed_at: datetime | None = None
