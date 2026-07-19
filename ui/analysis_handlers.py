"""Testable helpers for Streamlit analysis button handling."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ui.api_client import ApiClientError, BackendUnavailableError, run_preset_analysis
from ui.prompts import ANALYSIS_LABELS, get_analysis_prompt


def analysis_button_key(label: str) -> str:
    """Return a stable, unique Streamlit widget key for an analysis button."""
    slug = label.lower().replace(" ", "_")
    return f"analysis_button_{slug}"


def format_api_error(error: Exception) -> str:
    """Format an API client error for display in the UI."""
    if isinstance(error, ApiClientError) and error.status_code is not None:
        return f"[HTTP {error.status_code}] {error}"
    return str(error)


def store_analysis_result(
    results: dict[str, dict[str, Any]],
    label: str,
    payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Store one analysis result without removing existing results."""
    return {**results, label: payload}


def clear_analysis_error(
    errors: dict[str, str],
    label: str,
) -> dict[str, str]:
    """Remove a stored analysis error for the given label."""
    if label not in errors:
        return errors
    return {key: value for key, value in errors.items() if key != label}


def store_analysis_error(
    errors: dict[str, str],
    label: str,
    message: str,
) -> dict[str, str]:
    """Store an analysis error without removing other errors."""
    return {**errors, label: message}


def run_analysis_for_label(
    *,
    label: str,
    results: dict[str, dict[str, Any]],
    errors: dict[str, str],
    base_url: str,
    document_id: str,
    top_k: int,
    timeout: float,
    ask_fn: Callable[..., dict[str, Any]] = run_preset_analysis,
) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Run one preset analysis and return updated result/error state."""
    prompt = get_analysis_prompt(label)
    try:
        payload = ask_fn(
            base_url,
            document_id,
            prompt=prompt,
            top_k=top_k,
            timeout=timeout,
        )
    except (BackendUnavailableError, ApiClientError) as exc:
        return results, store_analysis_error(errors, label, format_api_error(exc))

    return store_analysis_result(results, label, payload), clear_analysis_error(errors, label)
