from io import BytesIO
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_metadata_endpoint_returns_uploaded_metadata() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Metadata test")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    response = client.get(f"/api/v1/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"] == document_id
    assert payload["filename"] == "rfp.pdf"
    assert payload["content_type"] == "application/pdf"
    assert payload["size_bytes"] > 0
    assert payload["status"] == "uploaded"
    assert payload["page_count"] is None
    assert payload["characters"] is None
    assert payload["created_at"]
    assert "text" not in payload


def test_metadata_endpoint_returns_parsed_metadata() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(make_text_pdf("Parsed metadata test")), "application/pdf")},
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    parse_response = client.post(f"/api/v1/documents/{document_id}/parse")
    assert parse_response.status_code == 200
    parsed_payload = parse_response.json()

    response = client.get(f"/api/v1/documents/{document_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "parsed"
    assert payload["page_count"] == parsed_payload["page_count"]
    assert payload["characters"] == parsed_payload["characters"]
    assert "text" not in payload


def test_metadata_endpoint_returns_404_for_unknown_document() -> None:
    response = client.get(f"/api/v1/documents/{uuid4()}")

    assert response.status_code == 404
