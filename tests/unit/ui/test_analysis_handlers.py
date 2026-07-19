import pytest

from ui.analysis_handlers import (
    analysis_button_key,
    format_api_error,
    run_analysis_for_label,
    store_analysis_result,
)
from ui.api_client import ApiClientError
from ui.prompts import ANALYSIS_LABELS, ANALYSIS_PROMPTS, get_analysis_prompt


def test_analysis_button_keys_are_unique() -> None:
    keys = [analysis_button_key(label) for label in ANALYSIS_LABELS]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize("label", ANALYSIS_LABELS)
def test_get_analysis_prompt_returns_expected_prompt(label: str) -> None:
    assert get_analysis_prompt(label) == ANALYSIS_PROMPTS[label]


def test_store_analysis_result_preserves_existing_results() -> None:
    results = {
        "Executive Summary": {"answer": "summary", "sources": []},
    }

    updated = store_analysis_result(
        results,
        "Risks",
        {"answer": "risk analysis", "sources": []},
    )

    assert updated["Executive Summary"]["answer"] == "summary"
    assert updated["Risks"]["answer"] == "risk analysis"


def test_run_analysis_for_label_stores_result_separately() -> None:
    def fake_ask(
        base_url: str,
        document_id: str,
        *,
        prompt: str,
        top_k: int,
        timeout: float,
    ) -> dict[str, object]:
        return {
            "document_id": document_id,
            "question": prompt,
            "answer": f"answer for {prompt}",
            "sources": [],
            "status": "answered",
        }

    existing = {
        "Executive Summary": {"answer": "existing summary", "sources": []},
    }
    results, errors = run_analysis_for_label(
        label="Requirements",
        results=existing,
        errors={},
        base_url="http://localhost:8000",
        document_id="doc-123",
        top_k=7,
        timeout=30.0,
        ask_fn=fake_ask,
    )

    assert results["Executive Summary"]["answer"] == "existing summary"
    assert "functional and non-functional requirements" in results["Requirements"]["answer"]
    assert errors == {}


def test_run_analysis_for_label_passes_selected_top_k_and_document_id() -> None:
    captured: dict[str, object] = {}

    def fake_ask(
        base_url: str,
        document_id: str,
        *,
        prompt: str,
        top_k: int,
        timeout: float,
    ) -> dict[str, object]:
        captured.update(
            {
                "base_url": base_url,
                "document_id": document_id,
                "prompt": prompt,
                "top_k": top_k,
                "timeout": timeout,
            }
        )
        return {"answer": "ok", "sources": []}

    run_analysis_for_label(
        label="Risks",
        results={},
        errors={},
        base_url="http://localhost:8000",
        document_id="doc-456",
        top_k=12,
        timeout=45.0,
        ask_fn=fake_ask,
    )

    assert captured["document_id"] == "doc-456"
    assert captured["top_k"] == 12
    assert captured["prompt"] == ANALYSIS_PROMPTS["Risks"]


def test_run_analysis_for_label_supports_multiple_analyses_in_one_session() -> None:
    def fake_ask(
        _base_url: str,
        _document_id: str,
        *,
        prompt: str,
        top_k: int,
        timeout: float,
    ) -> dict[str, object]:
        return {"answer": prompt, "sources": []}

    results: dict[str, dict[str, object]] = {}
    errors: dict[str, str] = {}

    for label in ("Executive Summary", "Risks", "Assumptions"):
        results, errors = run_analysis_for_label(
            label=label,
            results=results,
            errors=errors,
            base_url="http://localhost:8000",
            document_id="doc-789",
            top_k=5,
            timeout=30.0,
            ask_fn=fake_ask,
        )

    assert set(results) == {"Executive Summary", "Risks", "Assumptions"}
    assert errors == {}


def test_run_analysis_for_label_stores_backend_error_without_dropping_results() -> None:
    existing = {
        "Executive Summary": {"answer": "existing summary", "sources": []},
    }

    def failing_ask(*args: object, **kwargs: object) -> dict[str, object]:
        raise ApiClientError("OpenRouter answer request failed", status_code=422)

    results, errors = run_analysis_for_label(
        label="Requirements",
        results=existing,
        errors={},
        base_url="http://localhost:8000",
        document_id="doc-123",
        top_k=5,
        timeout=30.0,
        ask_fn=failing_ask,
    )

    assert results == existing
    assert errors["Requirements"] == "[HTTP 422] OpenRouter answer request failed"


def test_format_api_error_includes_status_code() -> None:
    message = format_api_error(ApiClientError("provider failed", status_code=422))

    assert message == "[HTTP 422] provider failed"


def test_analysis_labels_match_prompt_keys() -> None:
    assert set(ANALYSIS_LABELS) == set(ANALYSIS_PROMPTS)
