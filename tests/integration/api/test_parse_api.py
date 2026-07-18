from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.pdf import make_blank_pdf, make_empty_pdf, make_text_pdf

client = TestClient(app)


def test_parse_endpoint_returns_extracted_text() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Integration test text")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["status"] == "parsed"
    assert payload["page_count"] == 1
    assert payload["pages"] == 1
    assert "Integration test text" in payload["text"]
    assert payload["characters"] == len(payload["text"])


def test_parse_endpoint_returns_404_for_missing_document() -> None:
    response = client.post(f"/api/v1/documents/{uuid4()}/parse")

    assert response.status_code == 404


def test_parse_endpoint_returns_404_for_missing_document_id_string() -> None:
    response = client.post("/api/v1/documents/missing-id/parse")

    assert response.status_code == 404


def test_parse_endpoint_returns_422_for_invalid_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-1.4 broken"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 422
    assert "Unable to read PDF file" in response.json()["detail"]


def test_parse_endpoint_returns_422_for_invalid_pdf_bytes() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("broken.pdf", BytesIO(b"%PDF-broken"), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 422
    assert "Unable to read PDF file" in response.json()["detail"]


def test_parse_endpoint_returns_422_for_empty_pdf() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("blank.pdf", BytesIO(make_blank_pdf()), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 422
    assert "no extractable text" in response.json()["detail"]


def test_parse_endpoint_returns_422_for_empty_pdf_helper() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.pdf", BytesIO(make_empty_pdf()), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.post(f"/api/v1/documents/{document_id}/parse")

    assert response.status_code == 422
    assert "no extractable text" in response.json()["detail"]
