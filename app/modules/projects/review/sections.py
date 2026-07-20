"""Review category definitions for evidence-based proposal gap analysis."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewCategoryDefinition:
    """Configuration for one review category."""

    key: str
    title: str
    search_query: str
    generation_prompt: str


JSON_RESPONSE_SUFFIX = (
    "\n\nRespond with JSON only using this shape:\n"
    '{"summary":"...", "findings":[{"title":"...", "description":"...", '
    '"severity":"low|medium|high|critical", "recommendation":"...", '
    '"coverage_status":"covered|partially_covered|missing|null", '
    '"proposal_section":"...", "source_document":"...", "page": 1}]}\n'
    "Use severity and coverage_status faithfully. Base every finding on the supplied context only."
)


REVIEW_CATEGORY_DEFINITIONS: tuple[ReviewCategoryDefinition, ...] = (
    ReviewCategoryDefinition(
        key="executive_assessment",
        title="Executive Assessment",
        search_query="executive summary business objectives customer goals proposal overview",
        generation_prompt=(
            "Review the proposal against the RFP/source documents. Provide an executive assessment "
            "of proposal quality, completeness, and delivery readiness."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="coverage_score",
        title="Coverage Score",
        search_query="functional requirements non-functional requirements scope deliverables",
        generation_prompt=(
            "Perform coverage analysis comparing RFP requirements to the proposal. "
            "For each finding, set coverage_status to covered, partially_covered, or missing."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="missing_requirements",
        title="Missing Requirements",
        search_query="mandatory requirements shall must functional requirements acceptance criteria",
        generation_prompt=(
            "Identify requirements present in the source documents but missing or weak in the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="missing_integrations",
        title="Missing Integrations",
        search_query="integrations ERP email telephony API identity payment systems",
        generation_prompt=(
            "Identify integrations required by the source documents that are missing from the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="missing_non_functional_requirements",
        title="Missing Non-functional Requirements",
        search_query="availability security GDPR performance scalability SLA backup disaster recovery",
        generation_prompt=(
            "Identify non-functional requirements in the source documents absent from the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="contradictions",
        title="Contradictions",
        search_query="timeline budget pricing integration scope assumptions dependencies numbers dates",
        generation_prompt=(
            "Detect contradictions: conflicting numbers, timelines, integrations, dependencies, "
            "or unsupported claims between source documents and the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="weak_assumptions",
        title="Weak Assumptions",
        search_query="assumptions dependencies prerequisites vendor customer responsibilities",
        generation_prompt=(
            "Identify weak, vague, or risky assumptions in the proposal versus source evidence."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="weak_risks",
        title="Weak Risks",
        search_query="risks mitigation delivery commercial technical issues",
        generation_prompt=(
            "Identify weak or missing risk treatment in the proposal compared to source documents."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="weak_timeline",
        title="Weak Timeline",
        search_query="timeline schedule milestones phases UAT go-live delivery plan",
        generation_prompt=(
            "Identify timeline gaps, unrealistic milestones, or missing phases in the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="weak_scope",
        title="Weak Scope",
        search_query="scope deliverables out of scope boundaries exclusions work packages",
        generation_prompt=(
            "Identify scope weaknesses, ambiguous boundaries, or missing deliverables in the proposal."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="improvement_suggestions",
        title="Improvement Suggestions",
        search_query="evaluation criteria vendor response submission requirements proposal quality",
        generation_prompt=(
            "Suggest concrete improvements to strengthen the proposal before customer submission."
        ) + JSON_RESPONSE_SUFFIX,
    ),
    ReviewCategoryDefinition(
        key="overall_readiness",
        title="Overall Readiness",
        search_query="acceptance criteria evaluation submission commercial terms readiness",
        generation_prompt=(
            "Assess overall proposal readiness for Delivery Manager review. "
            "Summarize blockers and readiness level."
        ) + JSON_RESPONSE_SUFFIX,
    ),
)


def review_category_keys() -> tuple[str, ...]:
    """Return ordered review category keys."""
    return tuple(category.key for category in REVIEW_CATEGORY_DEFINITIONS)


def get_review_category_definition(category_key: str) -> ReviewCategoryDefinition:
    """Return the definition for a review category key."""
    for category in REVIEW_CATEGORY_DEFINITIONS:
        if category.key == category_key:
            return category
    raise KeyError(category_key)
