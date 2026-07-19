from unittest.mock import MagicMock, patch

import httpx
import pytest

from ui.api_client import (
    ApiClientError,
    BackendUnavailableError,
    ask_question,
    check_health,
    get_platform_status,
    process_document,
    run_preset_analysis,
    upload_document,
)
from ui.prompts import ANALYSIS_PROMPTS


def test_check_health_returns_payload() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        payload = check_health("http://localhost:8000")

    assert payload == {"status": "ok"}


def test_get_platform_status_returns_provider_metadata() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "embedding_provider": "mock",
        "answer_provider": "openrouter",
        "answer_model": "openrouter/free",
        "app_environment": "development",
    }

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        payload = get_platform_status("http://localhost:8000")

    assert payload["answer_model"] == "openrouter/free"
    assert client.request.call_args[0][1] == "/api/v1/status"


def test_upload_document_sends_multipart_request() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "document_id": "doc-1",
        "filename": "rfp.pdf",
        "status": "uploaded",
    }

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        payload = upload_document(
            "http://localhost:8000",
            filename="rfp.pdf",
            content=b"%PDF-test",
        )

    assert payload["document_id"] == "doc-1"
    _, kwargs = client.request.call_args
    assert kwargs["files"]["file"][0] == "rfp.pdf"


def test_process_document_runs_full_pipeline() -> None:
    stages: list[str] = []

    def fake_request(
        _client: httpx.Client,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        files: dict | None = None,
    ) -> dict:
        if path == "/api/v1/documents/upload":
            return {"document_id": "doc-1"}
        if path.endswith("/parse"):
            return {"document_id": "doc-1", "status": "parsed"}
        if path.endswith("/chunks"):
            return {"document_id": "doc-1", "chunk_count": 3}
        if path.endswith("/embeddings"):
            return {"document_id": "doc-1", "status": "embedded"}
        if path.endswith("/index"):
            return {"document_id": "doc-1", "chunks_indexed": 3, "status": "indexed"}
        if path.endswith("/doc-1") and method == "GET":
            return {
                "document_id": "doc-1",
                "filename": "rfp.pdf",
                "size_bytes": 1234,
            }
        raise AssertionError(f"Unexpected request: {method} {path}")

    with patch("ui.api_client._request", side_effect=fake_request):
        result = process_document(
            "http://localhost:8000",
            filename="rfp.pdf",
            content=b"pdf",
            progress_callback=stages.append,
        )

    assert result.document_id == "doc-1"
    assert result.chunk_count == 3
    assert result.chunks_indexed == 3
    assert stages[0] == "Uploading..."
    assert stages[-1] == "Ready."


def test_run_preset_analysis_uses_ask_endpoint() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "document_id": "doc-1",
        "question": ANALYSIS_PROMPTS["Risks"],
        "answer": "Risk analysis",
        "sources": [],
        "status": "answered",
    }

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        payload = run_preset_analysis(
            "http://localhost:8000",
            "doc-1",
            prompt=ANALYSIS_PROMPTS["Risks"],
            top_k=8,
        )

    assert payload["answer"] == "Risk analysis"
    _, kwargs = client.request.call_args
    assert kwargs["json"] == {"question": ANALYSIS_PROMPTS["Risks"], "top_k": 8}
    assert "/ask" in client.request.call_args[0][1]


def test_ask_question_posts_expected_payload() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "document_id": "doc-1",
        "question": "What is the scope?",
        "answer": "Scope answer",
        "sources": [],
        "status": "answered",
    }

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        payload = ask_question(
            "http://localhost:8000",
            "doc-1",
            question="What is the scope?",
            top_k=4,
        )

    assert payload["answer"] == "Scope answer"
    _, kwargs = client.request.call_args
    assert kwargs["json"] == {"question": "What is the scope?", "top_k": 4}


def test_backend_connection_failure_raises_actionable_error() -> None:
    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.side_effect = httpx.ConnectError("connection refused")

        with pytest.raises(BackendUnavailableError, match="Unable to reach the backend API"):
            check_health("http://localhost:8000")


def test_api_error_extracts_response_detail() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = {"detail": "Parse failed"}

    with patch("ui.api_client.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.request.return_value = mock_response

        with pytest.raises(ApiClientError, match="Parse failed") as exc_info:
            upload_document(
                "http://localhost:8000",
                filename="rfp.pdf",
                content=b"pdf",
            )

    assert exc_info.value.status_code == 422


def test_analysis_prompts_include_required_presets() -> None:
    assert "Executive Summary" in ANALYSIS_PROMPTS
    assert "Requirements" in ANALYSIS_PROMPTS
    assert "Risks" in ANALYSIS_PROMPTS
    assert "Generate an executive summary of this RFP." in ANALYSIS_PROMPTS["Executive Summary"]
