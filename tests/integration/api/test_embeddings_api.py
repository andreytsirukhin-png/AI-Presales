from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.infrastructure.embeddings.mock_provider import MOCK_EMBEDDING_DIMENSION
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_embeddings_endpoint_returns_summary_for_uploaded_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Embedding integration test")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/embeddings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["status"] == "embedded"
    assert payload["embedding_dimension"] == MOCK_EMBEDDING_DIMENSION
    assert payload["chunk_count"] >= 1
    assert set(payload.keys()) == {
        "document_id",
        "chunk_count",
        "embedding_dimension",
        "status",
    }


def test_embeddings_endpoint_returns_404_for_unknown_document() -> None:
    response = client.post(f"/api/v1/documents/{uuid4()}/embeddings")

    assert response.status_code == 404


def test_embeddings_endpoint_returns_422_for_invalid_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/embeddings")

    assert response.status_code == 422
    assert "Unable to read PDF file" in response.json()["detail"]
