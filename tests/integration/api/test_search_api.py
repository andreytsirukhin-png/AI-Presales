from io import BytesIO
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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


def test_search_endpoint_works_after_upload_and_index() -> None:
    document_id = _upload_and_index("Search integration test for ERP integrations")

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "What integrations are required?", "top_k": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["query"] == "What integrations are required?"
    assert payload["result_count"] == len(payload["results"])
    assert payload["result_count"] >= 1
    assert set(payload.keys()) == {"document_id", "query", "result_count", "results"}
    assert set(payload["results"][0].keys()) == {"chunk_index", "text", "score", "metadata"}
    assert payload["results"][0]["metadata"] is not None
    assert "document_name" in payload["results"][0]["metadata"]


def test_search_results_are_sorted_by_score_descending() -> None:
    document_id = _upload_and_index("Sorted semantic search validation text")

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "semantic search validation", "top_k": 5},
    )

    assert response.status_code == 200
    scores = [result["score"] for result in response.json()["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_endpoint_returns_404_for_unknown_document() -> None:
    response = client.post(
        f"/api/v1/documents/{uuid4()}/search",
        json={"query": "missing document", "top_k": 5},
    )

    assert response.status_code == 404


def test_search_endpoint_returns_404_for_uploaded_but_not_indexed_document() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Not indexed yet")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "Not indexed yet", "top_k": 5},
    )

    assert response.status_code == 404


def test_search_endpoint_returns_422_for_empty_query() -> None:
    document_id = _upload_and_index("Empty query validation")

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "", "top_k": 5},
    )

    assert response.status_code == 422


@pytest.mark.parametrize("top_k", [0, 51])
def test_search_endpoint_returns_422_for_invalid_top_k(top_k: int) -> None:
    document_id = _upload_and_index("Invalid top_k validation")

    response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "validation", "top_k": top_k},
    )

    assert response.status_code == 422


def test_existing_index_endpoint_remains_compatible() -> None:
    document_id = _upload_and_index("Backward compatible index")

    response = client.post(f"/api/v1/documents/{document_id}/index")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"document_id", "chunks_indexed", "status"}
