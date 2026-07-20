from datetime import UTC, datetime

from app.modules.projects.schemas.proposal import Proposal, ProposalSection
from app.modules.projects.services.proposal_export import proposal_to_docx_bytes, proposal_to_markdown


def _sample_proposal() -> Proposal:
    generated_at = datetime.now(UTC)
    section = ProposalSection(
        key="executive_summary",
        title="Executive Summary",
        content="This is the executive summary.",
        citations=[],
        sources=[],
        generated_at=generated_at,
        status="generated",
    )
    return Proposal(
        project_id="p1",
        project_name="Demo",
        generated_at=generated_at,
        sections=[section],
    )


def test_proposal_to_markdown_includes_section_title() -> None:
    markdown = proposal_to_markdown(_sample_proposal())
    assert "## Executive Summary" in markdown
    assert "This is the executive summary." in markdown


def test_proposal_to_docx_bytes_is_non_empty() -> None:
    docx_bytes = proposal_to_docx_bytes(_sample_proposal())
    assert docx_bytes.startswith(b"PK")
