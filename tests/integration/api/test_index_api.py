from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_index_endpoint_returns_summary_for_uploaded_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Index integration test")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/index")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["status"] == "indexed"
    assert payload["chunks_indexed"] >= 1
    assert set(payload.keys()) == {"document_id", "chunks_indexed", "status"}


def test_index_endpoint_returns_404_for_unknown_document() -> None:
    response = client.post(f"/api/v1/documents/{uuid4()}/index")

    assert response.status_code == 404


def test_index_endpoint_returns_422_for_invalid_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/index")

    assert response.status_code == 422
    assert "Unable to read PDF file" in response.json()["detail"]
