from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.dependencies import clear_dependency_caches
from app.main import app
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


def test_index_and_search_persist_after_vector_store_reload(
    tmp_path,
    monkeypatch,
) -> None:
    persist_path = tmp_path / "vector_store"
    override_settings = Settings(
        embedding_provider="mock",
        embedding_dimension=16,
        vector_store="chroma",
        vector_db_path=str(persist_path),
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        upload_response = client.post(
            "/api/v1/documents/upload",
            files={
                "file": (
                    "rfp.pdf",
                    make_text_pdf(
                        "CRM integration requirements include ERP connectivity and SSO."
                    ),
                    "application/pdf",
                )
            },
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        for step in ("parse", "chunks", "embeddings", "index"):
            response = client.post(f"/api/v1/documents/{document_id}/{step}")
            assert response.status_code == 200

        clear_dependency_caches()

        search_response = client.post(
            f"/api/v1/documents/{document_id}/search",
            json={"query": "ERP integration", "top_k": 3},
        )
        assert search_response.status_code == 200
        assert search_response.json()["result_count"] >= 1
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()
