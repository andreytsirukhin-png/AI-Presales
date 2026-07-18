from enum import Enum

from pydantic import BaseModel, Field


class RequirementType(str, Enum):
    functional = "functional"
    non_functional = "non_functional"
    integration = "integration"
    data = "data"
    security = "security"
    commercial = "commercial"
    delivery = "delivery"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Evidence(BaseModel):
    quote: str = Field(description="Short source excerpt supporting the finding")
    page: int | None = None
    section: str | None = None


class Requirement(BaseModel):
    id: str
    title: str
    description: str
    type: RequirementType
    mandatory: bool = True
    evidence: list[Evidence]


class ClarificationQuestion(BaseModel):
    id: str
    category: str
    question: str
    rationale: str
    priority: Severity
    related_requirement_ids: list[str] = []


class Risk(BaseModel):
    id: str
    title: str
    description: str
    probability: Severity
    impact: Severity
    mitigation: str
    evidence: list[Evidence] = []


class Assumption(BaseModel):
    id: str
    statement: str
    validation_needed: bool = True
    related_requirement_ids: list[str] = []


class AnalysisResult(BaseModel):
    document_summary: str
    requirements: list[Requirement]
    clarification_questions: list[ClarificationQuestion]
    risks: list[Risk]
    assumptions: list[Assumption]
    confidence: float = Field(ge=0, le=1)
