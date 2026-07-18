from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_chunks_endpoint_returns_chunks_for_uploaded_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Chunk integration test")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/chunks")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["chunk_count"] == len(payload["chunks"])
    assert payload["chunk_count"] >= 1
    assert payload["chunks"][0]["index"] == 0
    assert "Chunk integration test" in payload["chunks"][0]["text"]


def test_chunks_response_excludes_parse_fields() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Metadata-safe chunking")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/chunks")

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"document_id", "chunk_count", "chunks"}
    assert "text" not in payload
    assert "status" not in payload
    assert "pages" not in payload
    assert "page_count" not in payload
    assert "characters" not in payload


def test_chunks_endpoint_returns_404_for_unknown_document() -> None:
    response = client.post(f"/api/v1/documents/{uuid4()}/chunks")

    assert response.status_code == 404


def test_chunks_endpoint_returns_422_for_invalid_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/chunks")

    assert response.status_code == 422
    assert "Unable to read PDF file" in response.json()["detail"]


def test_existing_upload_endpoint_remains_compatible() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Backward compatible upload")), "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"document_id", "filename", "status"}


def test_existing_parse_endpoint_remains_compatible() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Backward compatible parse")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "parsed"
    assert "text" in payload
    assert "page_count" in payload


def test_existing_metadata_endpoint_remains_compatible() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Backward compatible metadata")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/api/v1/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["status"] == "uploaded"
    assert "text" not in payload
