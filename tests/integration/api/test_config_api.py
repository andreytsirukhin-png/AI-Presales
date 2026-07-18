from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_application_starts_with_default_settings() -> None:
    settings = get_settings()

    assert settings.app_name == "AI Presales"
    assert settings.storage_backend == "local"
    assert settings.embedding_provider == "mock"


def test_upload_index_search_works_with_default_settings() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Default settings search flow")),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    index_response = client.post(f"/api/v1/documents/{document_id}/index")
    assert index_response.status_code == 200

    search_response = client.post(
        f"/api/v1/documents/{document_id}/search",
        json={"query": "Default settings search flow", "top_k": 5},
    )

    assert search_response.status_code == 200
    assert search_response.json()["result_count"] >= 1


def test_upload_index_ask_works_with_default_settings() -> None:
    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Default settings ask flow")),
                "application/pdf",
            )
        },
    )
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]

    index_response = client.post(f"/api/v1/documents/{document_id}/index")
    assert index_response.status_code == 200

    ask_response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "What is the ask flow?", "top_k": 5},
    )

    assert ask_response.status_code == 200
    assert ask_response.json()["status"] == "answered"


def test_custom_temporary_storage_path_works(tmp_path: Path) -> None:
    override_settings = Settings(storage_path=str(tmp_path / "custom-storage"))

    app.dependency_overrides[get_settings] = lambda: override_settings
    try:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "rfp.pdf",
                    BytesIO(make_text_pdf("Custom storage path validation")),
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        assert (tmp_path / "custom-storage" / f"{document_id}.pdf").is_file()
    finally:
        app.dependency_overrides.clear()


def test_existing_upload_response_contract_remains_unchanged() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rfp.pdf",
                BytesIO(make_text_pdf("Upload contract validation")),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert set(response.json().keys()) == {"document_id", "filename", "status"}
