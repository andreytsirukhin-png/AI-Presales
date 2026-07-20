from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.dependencies import get_answer_provider
from app.infrastructure.answers.mock_provider import MockAnswerProvider
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def _create_project(name: str = "Demo RFP Workspace") -> str:
    response = client.post(
        "/api/v1/projects",
        json={"project_name": name, "description": "US017 integration test"},
    )
    assert response.status_code == 200
    return response.json()["project_id"]


def _upload_to_project(project_id: str, filename: str, text: str) -> str:
    response = client.post(
        f"/api/v1/projects/{project_id}/documents",
        files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "indexed"
    assert payload["chunks_indexed"] >= 1
    return payload["document_id"]


def test_project_crud_and_document_upload_auto_indexes() -> None:
    project_id = _create_project()

    list_response = client.get("/api/v1/projects")
    assert list_response.status_code == 200
    assert list_response.json()["count"] >= 1

    get_response = client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["document_count"] == 0

    doc_a = _upload_to_project(project_id, "RFP.pdf", "CRM integration requirements for ERP")
    doc_b = _upload_to_project(
        project_id,
        "Appendix-A.pdf",
        "Appendix pricing and commercial assumptions for CRM rollout",
    )

    documents = client.get(f"/api/v1/projects/{project_id}/documents").json()
    assert documents["count"] == 2
    assert {doc_a, doc_b} == {item["document_id"] for item in documents["documents"]}

    stats = client.get(f"/api/v1/projects/{project_id}/statistics").json()
    assert stats["document_count"] == 2
    assert stats["indexed_chunks"] >= 2


def test_project_search_returns_results_from_multiple_documents() -> None:
    app.dependency_overrides[get_answer_provider] = lambda: MockAnswerProvider()
    try:
        project_id = _create_project("Cross-doc search")
        _upload_to_project(project_id, "RFP.pdf", "Primary CRM integration and ERP connectivity")
        _upload_to_project(project_id, "Appendix-A.pdf", "Appendix A pricing model and licensing")

        search_response = client.post(
            f"/api/v1/projects/{project_id}/search",
            json={"query": "pricing and integration", "top_k": 5},
        )
        assert search_response.status_code == 200
        results = search_response.json()["results"]
        assert results
        document_names = {
            (result.get("metadata") or {}).get("document_name")
            for result in results
            if result.get("metadata")
        }
        assert len(document_names) >= 2

        ask_response = client.post(
            f"/api/v1/projects/{project_id}/ask",
            json={"question": "What pricing and integration details exist?", "top_k": 5},
        )
        assert ask_response.status_code == 200
        citations = ask_response.json()["citations"]
        assert citations
        cited_documents = {citation["document"] for citation in citations}
        assert len(cited_documents) >= 2
    finally:
        app.dependency_overrides.clear()


def test_delete_project_document_and_project() -> None:
    project_id = _create_project("Delete flow")
    document_id = _upload_to_project(project_id, "temp.pdf", "Temporary document content")

    delete_doc = client.delete(f"/api/v1/projects/{project_id}/documents/{document_id}")
    assert delete_doc.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}").json()["document_count"] == 0

    delete_project = client.delete(f"/api/v1/projects/{project_id}")
    assert delete_project.status_code == 204
    missing = client.get(f"/api/v1/projects/{project_id}")
    assert missing.status_code == 404
