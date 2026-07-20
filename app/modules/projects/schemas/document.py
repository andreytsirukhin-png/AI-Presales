from pydantic import BaseModel, Field

from app.modules.documents.schemas.document import DocumentMetadata


class ProjectDocumentUploadResponse(BaseModel):
    """Response after uploading and indexing a document in a project."""

    project_id: str
    document_id: str
    filename: str
    status: str
    chunks_indexed: int = Field(..., ge=0)


class ProjectDocumentListResponse(BaseModel):
    """Documents belonging to a project."""

    project_id: str
    documents: list[DocumentMetadata]
    count: int = Field(..., ge=0)
