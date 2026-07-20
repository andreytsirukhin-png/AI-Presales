from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.infrastructure.answers.mock_provider import FALLBACK_ANSWER
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def _upload_and_index(text: str) -> str:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf(text)), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    index_response = client.post(f"/api/v1/documents/{document_id}/index")
    assert index_response.status_code == 200

    return document_id


def test_ask_endpoint_works_after_upload_and_index() -> None:
    document_id = _upload_and_index("Ask integration test for ERP integrations")

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "What integrations are required?", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["question"] == "What integrations are required?"
    assert payload["status"] == "answered"
    assert payload["answer"]
    assert payload["sources"]
    assert payload["citations"]
    assert set(payload.keys()) == {
        "document_id",
        "question",
        "answer",
        "sources",
        "citations",
        "status",
    }
    assert set(payload["sources"][0].keys()) == {"chunk_index", "text", "score", "metadata"}
    assert set(payload["citations"][0].keys()) == {
        "document",
        "page",
        "score",
        "chunk_index",
        "chunk_id",
    }


def test_ask_sources_match_semantic_search_output() -> None:
    document_id = _upload_and_index("Sources should match semantic search output")
    question = "semantic search output"
    top_k = 3

    search_response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": question, "top_k": top_k},
    )
    ask_response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": question, "top_k": top_k},
    )

    assert search_response.status_code == 200
    assert ask_response.status_code == 200
    assert ask_response.json()["sources"] == search_response.json()["results"]


def test_ask_answer_is_grounded_only_in_returned_sources() -> None:
    document_id = _upload_and_index("Grounded answer validation for integrations")

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "What integrations are required?", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    usable_source_text = " ".join(
        source["text"].strip()
        for source in payload["sources"]
        if source["text"].strip()
    )

    if usable_source_text:
        assert payload["answer"] == f"Based on the indexed document: {usable_source_text}"
    else:
        assert payload["answer"] == FALLBACK_ANSWER


def test_ask_endpoint_returns_404_for_unknown_document() -> None:
    response = client.post(
        f"/api/v1/documents/{uuid4()}/ask",
        json={"question": "missing document", "top_k": 5},
    )

    assert response.status_code == 404


def test_ask_endpoint_returns_404_for_uploaded_but_not_indexed_document() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Not indexed yet")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "Not indexed yet", "top_k": 5},
    )

    assert response.status_code == 404


def test_ask_endpoint_returns_422_for_empty_question() -> None:
    document_id = _upload_and_index("Empty question validation")

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "", "top_k": 5},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("top_k", [0, 51])
def test_ask_endpoint_returns_422_for_invalid_top_k(top_k: int) -> None:
    document_id = _upload_and_index("Invalid top_k validation")

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "validation", "top_k": top_k},
    )

    assert response.status_code == 422


def test_existing_search_endpoint_remains_compatible() -> None:
    document_id = _upload_and_index("Backward compatible search")

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "Backward compatible search", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"document_id", "query", "result_count", "results"}
