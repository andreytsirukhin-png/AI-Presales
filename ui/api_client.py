"""HTTP client helpers for the Streamlit demo."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

PROCESS_STAGES = (
    "Uploading...",
    "Parsing...",
    "Creating chunks...",
    "Generating embeddings...",
    "Indexing...",
    "Ready.",
)


class ApiClientError(Exception):
    """Raised when the backend returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class BackendUnavailableError(ApiClientError):
    """Raised when the backend cannot be reached."""


@dataclass(frozen=True)
class ProcessDocumentResult:
    """Summary of a completed document processing pipeline."""

    document_id: str
    filename: str
    size_bytes: int
    chunk_count: int
    chunks_indexed: int
    status: str


def _extract_error_detail(response: httpx.Response) -> str:
    """Extract a concise error message from an API response."""
    try:
        payload = response.json()
    except ValueError:
        return response.text or f"Request failed with status {response.status_code}"

    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        first = detail[0]
        if isinstance(first, dict) and "msg" in first:
            return str(first["msg"])
    return f"Request failed with status {response.status_code}"


def _request(
    client: httpx.Client,
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
) -> dict[str, Any]:
    """Execute an HTTP request and return the JSON payload."""
    try:
        response = client.request(method, path, json=json, files=files)
    except httpx.TimeoutException as exc:
        raise BackendUnavailableError(
            "The backend request timed out. Check that the API is running.",
        ) from exc
    except httpx.RequestError as exc:
        raise BackendUnavailableError(
            "Unable to reach the backend API. Start FastAPI on the configured URL.",
        ) from exc

    if response.status_code >= 400:
        raise ApiClientError(
            _extract_error_detail(response),
            status_code=response.status_code,
        )
    return response.json()


def check_health(base_url: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """Check backend health."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", "/health")


def get_platform_status(base_url: str, *, timeout: float = 10.0) -> dict[str, Any]:
    """Return configured provider metadata from the backend."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", "/api/v1/status")


def upload_document(
    base_url: str,
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Upload a PDF document."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            "/api/v1/documents/upload",
            files={"file": (filename, content, content_type)},
        )


def parse_document(
    base_url: str,
    document_id: str,
    *,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Parse an uploaded document."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "POST", f"/api/v1/documents/{document_id}/parse")


def chunk_document(
    base_url: str,
    document_id: str,
    *,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Chunk a parsed document."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "POST", f"/api/v1/documents/{document_id}/chunks")


def embed_document(
    base_url: str,
    document_id: str,
    *,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Generate embeddings for a chunked document."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "POST", f"/api/v1/documents/{document_id}/embeddings")


def index_document(
    base_url: str,
    document_id: str,
    *,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Index embeddings for a document."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "POST", f"/api/v1/documents/{document_id}/index")


def get_document_metadata(
    base_url: str,
    document_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Fetch document metadata."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", f"/api/v1/documents/{document_id}")


def ask_question(
    base_url: str,
    document_id: str,
    *,
    question: str,
    top_k: int = 5,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Ask a question about an indexed document using the ask endpoint."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/documents/{document_id}/ask",
            json={"question": question, "top_k": top_k},
        )


def run_preset_analysis(
    base_url: str,
    document_id: str,
    *,
    prompt: str,
    top_k: int = 10,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Run a preset analysis by sending a specialized prompt to the ask endpoint."""
    return ask_question(
        base_url,
        document_id,
        question=prompt,
        top_k=top_k,
        timeout=timeout,
    )


def create_project(
    base_url: str,
    *,
    project_name: str,
    description: str = "",
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Create a workspace project."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            "/api/v1/projects",
            json={"project_name": project_name, "description": description},
        )


def list_projects(base_url: str, *, timeout: float = 30.0) -> dict[str, Any]:
    """List workspace projects."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", "/api/v1/projects")


def get_project_statistics(
    base_url: str,
    project_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Return project indexing statistics."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", f"/api/v1/projects/{project_id}/statistics")


def list_project_documents(
    base_url: str,
    project_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """List documents in a project."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", f"/api/v1/projects/{project_id}/documents")


def upload_project_document(
    base_url: str,
    project_id: str,
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
    timeout: float = 180.0,
) -> dict[str, Any]:
    """Upload and auto-index a PDF in a project workspace."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, content, content_type)},
        )


def delete_project_document(
    base_url: str,
    project_id: str,
    document_id: str,
    *,
    timeout: float = 30.0,
) -> None:
    """Delete one document from a project."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        response = client.delete(f"/api/v1/projects/{project_id}/documents/{document_id}")
        if response.status_code >= 400:
            raise ApiClientError(
                _extract_error_detail(response),
                status_code=response.status_code,
            )


def ask_project(
    base_url: str,
    project_id: str,
    *,
    question: str,
    top_k: int = 5,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Ask a question across all indexed documents in a project."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/ask",
            json={"question": question, "top_k": top_k},
        )


def run_preset_project_analysis(
    base_url: str,
    project_id: str,
    *,
    prompt: str,
    top_k: int = 10,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Run a preset analysis using project-wide retrieval."""
    return ask_project(
        base_url,
        project_id,
        question=prompt,
        top_k=top_k,
        timeout=timeout,
    )


def generate_project_proposal(
    base_url: str,
    project_id: str,
    *,
    top_k: int = 8,
    section_keys: list[str] | None = None,
    timeout: float = 300.0,
) -> dict[str, Any]:
    """Generate a cached commercial proposal for a project."""
    payload: dict[str, Any] = {"top_k": top_k}
    if section_keys is not None:
        payload["section_keys"] = section_keys
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/proposal",
            json=payload,
        )


def get_project_proposal(
    base_url: str,
    project_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Return a cached project proposal."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", f"/api/v1/projects/{project_id}/proposal")


def regenerate_project_proposal_sections(
    base_url: str,
    project_id: str,
    *,
    section_keys: list[str],
    top_k: int = 8,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Regenerate selected proposal sections."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/proposal/regenerate",
            json={"section_keys": section_keys, "top_k": top_k},
        )


def export_project_proposal(
    base_url: str,
    project_id: str,
    *,
    export_format: str = "markdown",
    timeout: float = 60.0,
) -> bytes:
    """Download a proposal export payload."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        response = client.get(
            f"/api/v1/projects/{project_id}/proposal/export",
            params={"format": export_format},
        )
        if response.status_code >= 400:
            raise ApiClientError(
                _extract_error_detail(response),
                status_code=response.status_code,
            )
        return response.content


def generate_project_review(
    base_url: str,
    project_id: str,
    *,
    top_k: int = 8,
    category_keys: list[str] | None = None,
    timeout: float = 600.0,
) -> dict[str, Any]:
    """Generate a cached proposal review report."""
    payload: dict[str, Any] = {"top_k": top_k}
    if category_keys is not None:
        payload["category_keys"] = category_keys
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/review",
            json=payload,
        )


def get_project_review(
    base_url: str,
    project_id: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Return a cached project review report."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(client, "GET", f"/api/v1/projects/{project_id}/review")


def regenerate_project_review_categories(
    base_url: str,
    project_id: str,
    *,
    category_keys: list[str],
    top_k: int = 8,
    timeout: float = 180.0,
) -> dict[str, Any]:
    """Regenerate selected review categories."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        return _request(
            client,
            "POST",
            f"/api/v1/projects/{project_id}/review/regenerate",
            json={"category_keys": category_keys, "top_k": top_k},
        )


def export_project_review(
    base_url: str,
    project_id: str,
    *,
    export_format: str = "markdown",
    timeout: float = 60.0,
) -> bytes:
    """Download a review export payload."""
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        response = client.get(
            f"/api/v1/projects/{project_id}/review/export",
            params={"format": export_format},
        )
        if response.status_code >= 400:
            raise ApiClientError(
                _extract_error_detail(response),
                status_code=response.status_code,
            )
        return response.content


def process_document(
    base_url: str,
    *,
    filename: str,
    content: bytes,
    content_type: str = "application/pdf",
    timeout: float = 120.0,
    progress_callback: Callable[[str], None] | None = None,
) -> ProcessDocumentResult:
    """Run the full upload-to-index pipeline through the HTTP API."""
    def notify(stage: str) -> None:
        if progress_callback is not None:
            progress_callback(stage)

    notify(PROCESS_STAGES[0])
    upload_payload = upload_document(
        base_url,
        filename=filename,
        content=content,
        content_type=content_type,
        timeout=timeout,
    )
    document_id = upload_payload["document_id"]

    notify(PROCESS_STAGES[1])
    parse_document(base_url, document_id, timeout=timeout)

    notify(PROCESS_STAGES[2])
    chunk_payload = chunk_document(base_url, document_id, timeout=timeout)

    notify(PROCESS_STAGES[3])
    embed_document(base_url, document_id, timeout=timeout)

    notify(PROCESS_STAGES[4])
    index_payload = index_document(base_url, document_id, timeout=timeout)

    notify(PROCESS_STAGES[5])
    metadata = get_document_metadata(base_url, document_id, timeout=timeout)
    return ProcessDocumentResult(
        document_id=document_id,
        filename=metadata.get("filename", filename),
        size_bytes=int(metadata.get("size_bytes", len(content))),
        chunk_count=int(chunk_payload.get("chunk_count", 0)),
        chunks_indexed=int(index_payload.get("chunks_indexed", 0)),
        status=index_payload.get("status", "indexed"),
    )
