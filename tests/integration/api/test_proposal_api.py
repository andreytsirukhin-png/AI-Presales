from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_answer_provider
from app.infrastructure.answers.mock_provider import MockAnswerProvider
from app.main import app
from app.modules.projects.proposal.sections import proposal_section_keys
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


class CountingAnswerProvider(MockAnswerProvider):
    """Mock provider that records how many LLM calls were made."""

    def __init__(self) -> None:
        super().__init__()
        self.call_count = 0

    def generate_answer(self, question: str, context_chunks: list) -> str:
        self.call_count += 1
        return super().generate_answer(question, context_chunks)


def _setup_project_with_two_documents() -> tuple[str, CountingAnswerProvider]:
    provider = CountingAnswerProvider()
    app.dependency_overrides[get_answer_provider] = lambda: provider

    create = client.post(
        "/api/v1/projects",
        json={"project_name": "Proposal Test", "description": "US018"},
    )
    assert create.status_code == 200
    project_id = create.json()["project_id"]

    for filename, text in (
        ("RFP.pdf", "CRM integration ERP delivery timeline assumptions risks"),
        ("Appendix-A.pdf", "Appendix pricing licensing commercial terms"),
    ):
        upload = client.post(
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
        )
        assert upload.status_code == 200

    return project_id, provider


def test_proposal_generation_caching_and_export() -> None:
    project_id, provider = _setup_project_with_two_documents()
    try:
        generate = client.post(
            f"/api/v1/projects/{project_id}/proposal",
            json={"top_k": 5},
        )
        assert generate.status_code == 200
        proposal = generate.json()["proposal"]
        assert len(proposal["sections"]) == len(proposal_section_keys())
        assert provider.call_count == len(proposal_section_keys())
        assert all(section["citations"] for section in proposal["sections"])

        cached = client.get(f"/api/v1/projects/{project_id}/proposal")
        assert cached.status_code == 200
        assert cached.json()["proposal"]["project_id"] == project_id

        regen = client.post(
            f"/api/v1/projects/{project_id}/proposal/regenerate",
            json={"section_keys": ["risks"], "top_k": 5},
        )
        assert regen.status_code == 200
        assert provider.call_count == len(proposal_section_keys()) + 1

        markdown = client.get(
            f"/api/v1/projects/{project_id}/proposal/export",
            params={"format": "markdown"},
        )
        assert markdown.status_code == 200
        assert "Executive Summary" in markdown.text

        delete = client.delete(f"/api/v1/projects/{project_id}/proposal")
        assert delete.status_code == 204
        missing = client.get(f"/api/v1/projects/{project_id}/proposal")
        assert missing.status_code == 404
    finally:
        app.dependency_overrides.clear()
