from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.documents.schemas.ask import AnswerCitation, AnswerSource


class ProposalSection(BaseModel):
    """One generated proposal section with traceable citations."""

    key: str = Field(..., description="Stable section identifier.")
    title: str = Field(..., description="Human-readable section title.")
    content: str = Field(..., description="Generated section body text.")
    citations: list[AnswerCitation] = Field(default_factory=list)
    sources: list[AnswerSource] = Field(
        default_factory=list,
        description="Retrieved chunks used as section context.",
    )
    generated_at: datetime = Field(..., description="UTC timestamp when the section was generated.")
    status: str = Field(..., description="Section generation status.")


class Proposal(BaseModel):
    """Cached commercial proposal for a project workspace."""

    project_id: str
    project_name: str
    generated_at: datetime
    sections: list[ProposalSection] = Field(default_factory=list)


class ProposalGenerateRequest(BaseModel):
    """Request to generate or refresh proposal sections."""

    top_k: int = Field(default=8, ge=1, le=20)
    section_keys: list[str] | None = Field(
        default=None,
        description="Optional subset of sections to generate; default is all sections.",
    )


class ProposalRegenerateRequest(BaseModel):
    """Request to regenerate selected cached sections."""

    section_keys: list[str] = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)


class ProposalResponse(BaseModel):
    """API response wrapping a project proposal."""

    proposal: Proposal
