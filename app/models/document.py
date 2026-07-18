from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response returned after a successful document upload."""

    document_id: str = Field(..., description="Unique identifier for the uploaded document.")
    filename: str = Field(..., description="Original filename supplied by the client.")
    status: str = Field(..., description="Upload lifecycle status.")
