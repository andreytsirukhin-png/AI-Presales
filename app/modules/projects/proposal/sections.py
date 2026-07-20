"""Proposal section definitions: retrieval queries and generation prompts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProposalSectionDefinition:
    """Configuration for one proposal section."""

    key: str
    title: str
    search_query: str
    generation_prompt: str


PROPOSAL_SECTION_DEFINITIONS: tuple[ProposalSectionDefinition, ...] = (
    ProposalSectionDefinition(
        key="executive_summary",
        title="Executive Summary",
        search_query="executive summary business objectives purpose scope customer goals",
        generation_prompt=(
            "Generate an Executive Summary for a commercial proposal responding to this RFP. "
            "Use only the supplied context. Be concise and suitable for a Delivery Manager review."
        ),
    ),
    ProposalSectionDefinition(
        key="business_understanding",
        title="Business Understanding",
        search_query="business objectives customer goals purpose background context",
        generation_prompt=(
            "Describe the Business Understanding section of the proposal: customer context, "
            "objectives, and drivers. Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="proposed_solution",
        title="Proposed Solution",
        search_query="solution architecture platform CRM system proposed approach",
        generation_prompt=(
            "Generate the Proposed Solution section: high-level solution overview and value. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="scope",
        title="Scope",
        search_query="scope of work deliverables in scope boundaries",
        generation_prompt=(
            "Generate the Scope section listing what is included in the engagement. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="assumptions",
        title="Assumptions",
        search_query="assumptions dependencies prerequisites vendor response",
        generation_prompt=(
            "Generate the Assumptions section required for estimation and delivery. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="risks",
        title="Risks",
        search_query="risks delivery commercial technical mitigation",
        generation_prompt=(
            "Generate the Risks section covering delivery and commercial risks. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="dependencies",
        title="Dependencies",
        search_query="dependencies customer third party prerequisites access",
        generation_prompt=(
            "Generate the Dependencies section: external and customer dependencies. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="integrations",
        title="Integrations",
        search_query="integrations ERP email telephony API identity payment",
        generation_prompt=(
            "Generate the Integrations section describing required system integrations. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="functional_requirements",
        title="Functional Requirements",
        search_query="functional requirements features CRM leads opportunities pipeline",
        generation_prompt=(
            "Summarize Functional Requirements addressed in the proposal. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="non_functional_requirements",
        title="Non-functional Requirements",
        search_query="non-functional availability security GDPR performance scalability SLA",
        generation_prompt=(
            "Summarize Non-functional Requirements (performance, security, availability). "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="project_team",
        title="Project Team",
        search_query="team staffing roles vendor response resources",
        generation_prompt=(
            "Generate the Project Team section: recommended roles and responsibilities. "
            "Use only the supplied context; if team details are missing, state what is unknown."
        ),
    ),
    ProposalSectionDefinition(
        key="delivery_approach",
        title="Delivery Approach",
        search_query="delivery methodology agile phases implementation approach",
        generation_prompt=(
            "Generate the Delivery Approach section: methodology and governance. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="timeline",
        title="Timeline",
        search_query="timeline schedule phases milestones project plan UAT go-live",
        generation_prompt=(
            "Generate the Timeline section with phases and milestones. "
            "Use only the supplied context."
        ),
    ),
    ProposalSectionDefinition(
        key="out_of_scope",
        title="Out of Scope",
        search_query="out of scope exclusions boundaries not included",
        generation_prompt=(
            "Generate the Out of Scope section clarifying exclusions. "
            "Use only the supplied context; infer reasonable exclusions only when supported."
        ),
    ),
    ProposalSectionDefinition(
        key="open_questions",
        title="Open Questions",
        search_query="clarification questions open items ambiguities submission",
        generation_prompt=(
            "Generate Open Questions for the customer before finalizing the proposal. "
            "Use only the supplied context."
        ),
    ),
)


def proposal_section_keys() -> tuple[str, ...]:
    """Return ordered section keys for full proposal generation."""
    return tuple(section.key for section in PROPOSAL_SECTION_DEFINITIONS)


def get_section_definition(section_key: str) -> ProposalSectionDefinition:
    """Return the definition for a section key."""
    for section in PROPOSAL_SECTION_DEFINITIONS:
        if section.key == section_key:
            return section
    raise KeyError(section_key)
