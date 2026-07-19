from io import BytesIO

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.dependencies import (
    build_answer_provider,
    clear_dependency_caches,
    get_answer_provider,
)
from app.core.exceptions import AnswerConfigurationError, AnswerProviderError
from app.infrastructure.answers.mock_provider import MockAnswerProvider
from app.infrastructure.answers.openai_provider import OpenAIAnswerProvider
from app.main import app
from app.modules.documents.schemas.search import SearchResult
from tests.helpers.pdf import make_text_pdf

client = TestClient(app)


class RecordingAnswerProvider(MockAnswerProvider):
    """Test double that records answer generation calls."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, list[SearchResult]]] = []

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        self.calls.append((question, context_chunks))
        return "override answer"


class FailingAnswerProvider:
    """Test double that raises an application-level answer error."""

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        raise AnswerProviderError("Simulated provider failure")


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


def test_dependency_override_can_replace_answer_provider() -> None:
    override_provider = RecordingAnswerProvider()
    app.dependency_overrides[get_answer_provider] = lambda: override_provider
    try:
        document_id = _upload_and_index("OpenAI answer override integration test")

        ask_response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": "What is tested?", "top_k": 5},
        )

        assert ask_response.status_code == 200
        assert ask_response.json()["answer"] == "override answer"
        assert len(override_provider.calls) == 1
        assert override_provider.calls[0][0] == "What is tested?"
        assert all(isinstance(chunk, SearchResult) for chunk in override_provider.calls[0][1])
    finally:
        app.dependency_overrides.clear()


def test_answer_provider_receives_only_retrieved_chunks() -> None:
    override_provider = RecordingAnswerProvider()
    app.dependency_overrides[get_answer_provider] = lambda: override_provider
    try:
        document_id = _upload_and_index("Retrieved chunks only validation")

        ask_response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": "Retrieved chunks only validation", "top_k": 2},
        )

        assert ask_response.status_code == 200
        assert len(override_provider.calls) == 1
        retrieved_chunks = override_provider.calls[0][1]
        assert len(retrieved_chunks) <= 2
        assert ask_response.json()["sources"] == [
            {
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "score": chunk.score,
            }
            for chunk in retrieved_chunks
        ]
    finally:
        app.dependency_overrides.clear()


def test_provider_errors_are_converted_to_http_422() -> None:
    app.dependency_overrides[get_answer_provider] = lambda: FailingAnswerProvider()
    try:
        document_id = _upload_and_index("Provider error mapping validation")

        ask_response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": "Provider error mapping validation", "top_k": 5},
        )

        assert ask_response.status_code == 422
        assert ask_response.json()["detail"] == "Simulated provider failure"
    finally:
        app.dependency_overrides.clear()


def test_mock_answer_mode_still_works_end_to_end() -> None:
    document_id = _upload_and_index("Mock answer mode compatibility")

    ask_response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        json={"question": "Mock answer mode compatibility", "top_k": 5},
    )

    assert ask_response.status_code == 200
    payload = ask_response.json()
    assert payload["status"] == "answered"
    assert payload["answer"].startswith("Based on the indexed document:")
    assert set(payload.keys()) == {
        "document_id",
        "question",
        "answer",
        "sources",
        "status",
    }


def test_openai_provider_build_requires_api_key_via_dependency_override() -> None:
    override_settings = Settings(
        answer_provider="openai",
        openai_api_key="",
    )
    app.dependency_overrides[get_settings] = lambda: override_settings
    clear_dependency_caches()
    try:
        with pytest.raises(AnswerConfigurationError) as exc_info:
            build_answer_provider(
                override_settings.answer_provider,
                override_settings.openai_api_key,
                override_settings.openai_chat_model,
                override_settings.openai_temperature,
                override_settings.openai_max_output_tokens,
                override_settings.openrouter_api_key,
                override_settings.openrouter_base_url,
                override_settings.openrouter_chat_model,
            )
        assert "OpenAI API key is required" in str(exc_info.value)
    finally:
        app.dependency_overrides.clear()
        clear_dependency_caches()


def test_openai_answer_provider_can_be_wired_with_dependency_override() -> None:
    class StubOpenAIAnswerProvider(OpenAIAnswerProvider):
        def __init__(self) -> None:
            self.calls: list[tuple[str, list[SearchResult]]] = []

        def generate_answer(
            self,
            question: str,
            context_chunks: list[SearchResult],
        ) -> str:
            self.calls.append((question, context_chunks))
            return "stub openai answer"

    stub_provider = StubOpenAIAnswerProvider()
    app.dependency_overrides[get_answer_provider] = lambda: stub_provider
    try:
        document_id = _upload_and_index("Stub OpenAI answer provider wiring")

        ask_response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": "Stub OpenAI answer provider wiring", "top_k": 3},
        )

        assert ask_response.status_code == 200
        assert ask_response.json()["answer"] == "stub openai answer"
        assert len(stub_provider.calls) == 1
    finally:
        app.dependency_overrides.clear()
