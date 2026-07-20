from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.documents.schemas.ask import AnswerCitation


class ReviewSeverity(str, Enum):
    """Finding severity for gap analysis."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


CoverageStatus = Literal["covered", "partially_covered", "missing"]


class ReviewFinding(BaseModel):
    """One evidence-based review finding."""

    title: str
    description: str
    severity: ReviewSeverity
    recommendation: str
    coverage_status: CoverageStatus | None = None
    proposal_section: str | None = None
    source_document: str | None = None
    page: int | None = Field(default=None, ge=1)
    citations: list[AnswerCitation] = Field(default_factory=list)


class ReviewCategoryResult(BaseModel):
    """Results for a single review category."""

    key: str
    title: str
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    generated_at: datetime
    status: str


class ReviewMetrics(BaseModel):
    """Aggregate metrics derived from review findings."""

    coverage_percent: float = Field(..., ge=0, le=100)
    requirements_covered: int = Field(..., ge=0)
    requirements_missing: int = Field(..., ge=0)
    critical_findings: int = Field(..., ge=0)
    average_severity_score: float = Field(..., ge=0)
    readiness_score: float = Field(..., ge=0, le=100)


class ReviewReport(BaseModel):
    """Cached proposal review for a project workspace."""

    project_id: str
    project_name: str
    proposal_generated_at: datetime | None = None
    generated_at: datetime
    metrics: ReviewMetrics
    categories: list[ReviewCategoryResult] = Field(default_factory=list)


class ReviewGenerateRequest(BaseModel):
    """Request to generate a proposal review."""

    top_k: int = Field(default=8, ge=1, le=20)
    category_keys: list[str] | None = None


class ReviewRegenerateRequest(BaseModel):
    """Request to regenerate selected review categories."""

    category_keys: list[str] = Field(..., min_length=1)
    top_k: int = Field(default=8, ge=1, le=20)


class ReviewResponse(BaseModel):
    """API wrapper for a review report."""

    review: ReviewReport
