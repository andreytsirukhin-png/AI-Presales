import json
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_answer_provider
from app.infrastructure.answers.mock_provider import MockAnswerProvider
from app.main import app
from app.modules.projects.review.sections import review_category_keys
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


class JsonReviewAnswerProvider(MockAnswerProvider):
    """Mock provider that returns JSON for review prompts and plain text for proposals."""

    def generate_answer(self, question: str, context_chunks: list) -> str:
        if "Respond with JSON only" in question:
            return json.dumps(
                {
                    "summary": "Structured review summary.",
                    "findings": [
                        {
                            "title": "Missing requirement",
                            "description": "Requirement not reflected in proposal.",
                            "severity": "high",
                            "recommendation": "Update proposal scope.",
                            "coverage_status": "missing",
                            "proposal_section": "Scope",
                            "source_document": "RFP.pdf",
                            "page": 3,
                        }
                    ],
                }
            )
        return super().generate_answer(question, context_chunks)


def _setup_project_with_proposal() -> str:
    app.dependency_overrides[get_answer_provider] = lambda: JsonReviewAnswerProvider()
    create = client.post(
        "/api/v1/projects",
        json={"project_name": "Review Test", "description": "US019"},
    )
    project_id = create.json()["project_id"]
    for filename, text in (
        ("RFP.pdf", "CRM ERP integration availability security requirements timeline"),
        ("Appendix-A.pdf", "Appendix pricing assumptions dependencies"),
    ):
        client.post(
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
        )
    proposal = client.post(f"/api/v1/projects/{project_id}/proposal", json={"top_k": 4})
    assert proposal.status_code == 200
    return project_id


def test_review_generation_caching_export_and_regenerate() -> None:
    project_id = _setup_project_with_proposal()
    try:
        generate = client.post(
            f"/api/v1/projects/{project_id}/review",
            json={"top_k": 4},
        )
        assert generate.status_code == 200
        review = generate.json()["review"]
        assert len(review["categories"]) == len(review_category_keys())
        assert review["metrics"]["coverage_percent"] >= 0
        assert any(category["findings"] for category in review["categories"])
        assert all(
            finding.get("severity")
            for category in review["categories"]
            for finding in category["findings"]
        )
        assert all(
            "citations" in finding
            for category in review["categories"]
            for finding in category["findings"]
        )
        assert any(
            finding.get("citations")
            for category in review["categories"]
            for finding in category["findings"]
        )

        cached = client.get(f"/api/v1/projects/{project_id}/review")
        assert cached.status_code == 200

        regen = client.post(
            f"/api/v1/projects/{project_id}/review/regenerate",
            json={"category_keys": ["contradictions"], "top_k": 4},
        )
        assert regen.status_code == 200

        markdown = client.get(
            f"/api/v1/projects/{project_id}/review/export",
            params={"format": "markdown"},
        )
        assert markdown.status_code == 200
        assert "Coverage" in markdown.text

        delete = client.delete(f"/api/v1/projects/{project_id}/review")
        assert delete.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_review_requires_proposal() -> None:
    create = client.post("/api/v1/projects", json={"project_name": "No proposal", "description": ""})
    project_id = create.json()["project_id"]
    response = client.post(f"/api/v1/projects/{project_id}/review", json={"top_k": 3})
    assert response.status_code == 404
