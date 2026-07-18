from io import BytesIO

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PDF_CONTENT = b"%PDF-1.4 api test content"


def test_upload_endpoint_accepts_pdf() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("rfp.pdf", BytesIO(PDF_CONTENT), "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "uploaded"
    assert payload["filename"] == "rfp.pdf"
    assert payload["document_id"]


def test_upload_endpoint_rejects_non_pdf() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", BytesIO(b"hello"), "text/plain")},
    )

    assert response.status_code == 415


def test_upload_endpoint_rejects_oversized_file() -> None:
    oversized_content = b"%PDF" + (b"x" * (25 * 1024 * 1024))

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large.pdf", BytesIO(oversized_content), "application/pdf")},
    )

    assert response.status_code == 413
