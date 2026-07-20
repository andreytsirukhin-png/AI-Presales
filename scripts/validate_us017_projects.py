#!/usr/bin/env python3
"""End-to-end validation for US017 project workspace and multi-document retrieval."""

from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.helpers.pdf import make_text_pdf

BASE_URL = os.environ.get("AI_PRESALES_API_BASE_URL", "http://127.0.0.1:8000")


def main() -> int:
    results: dict[str, object] = {"errors": []}
    client = httpx.Client(base_url=BASE_URL, timeout=180.0)

    create = client.post(
        "/api/v1/projects",
        json={
            "project_name": "US017 Validation Workspace",
            "description": "Multi-document retrieval validation",
        },
    )
    create.raise_for_status()
    project_id = create.json()["project_id"]
    results["project_id"] = project_id

    uploads: dict[str, str] = {}
    for filename, text in (
        ("RFP.pdf", "Enterprise CRM RFP with ERP integration requirements."),
        ("Appendix-A.pdf", "Appendix A commercial pricing and licensing assumptions."),
    ):
        response = client.post(
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
        )
        response.raise_for_status()
        uploads[filename] = response.json()["document_id"]
    results["uploads"] = uploads

    stats = client.get(f"/api/v1/projects/{project_id}/statistics").json()
    results["statistics"] = stats
    if stats.get("document_count", 0) < 2:
        results["errors"].append("expected at least two project documents")

    search = client.post(
        f"/api/v1/projects/{project_id}/search",
        json={"query": "pricing integration ERP", "top_k": 6},
    )
    search.raise_for_status()
    search_payload = search.json()
    cited_documents = {
        (item.get("metadata") or {}).get("document_name")
        for item in search_payload.get("results", [])
        if item.get("metadata")
    }
    results["search"] = {
        "result_count": search_payload.get("result_count"),
        "document_names": sorted(name for name in cited_documents if name),
    }
    if len(cited_documents) < 2:
        results["errors"].append("search did not return chunks from multiple documents")

    ask = client.post(
        f"/api/v1/projects/{project_id}/ask",
        json={"question": "Summarize integration and pricing requirements.", "top_k": 6},
    )
    if ask.status_code >= 400:
        results["errors"].append(f"ask failed: {ask.text}")
    else:
        ask_payload = ask.json()
        citation_docs = {item["document"] for item in ask_payload.get("citations", [])}
        results["ask"] = {
            "citation_count": len(ask_payload.get("citations", [])),
            "documents": sorted(citation_docs),
        }
        if len(citation_docs) < 2:
            results["errors"].append("citations did not span multiple documents")

    persistence = verify_project_persistence(project_id, client)
    results["persistence"] = persistence
    if persistence.get("required") and not persistence.get("persisted"):
        results["errors"].append("project persistence check failed")

    out_path = ROOT / "docs" / "validation-us017-projects.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("WROTE", out_path)
    print(json.dumps(results, indent=2))
    return 0 if not results["errors"] else 1


def verify_project_persistence(project_id: str, client: httpx.Client) -> dict[str, object]:
    """Verify indexed project chunks remain searchable after rebuilding the vector store."""
    from app.core.config import Settings, clear_settings_cache
    from app.core.dependencies import build_vector_store, clear_dependency_caches
    from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider

    status = client.get("/api/v1/status").json()
    if status.get("vector_store") != "chroma":
        return {"required": False, "skipped": True, "reason": status.get("vector_store")}

    clear_dependency_caches()
    clear_settings_cache()
    settings = Settings()
    store = build_vector_store(settings.vector_store, settings.vector_db_path)
    provider = MockEmbeddingProvider(dimension=settings.embedding_dimension)
    project = client.get(f"/api/v1/projects/{project_id}").json()
    document_ids = [
        document["document_id"]
        for document in client.get(f"/api/v1/projects/{project_id}/documents").json()["documents"]
    ]
    hits = store.search_documents(document_ids, provider.embed("integration pricing"), top_k=3)
    return {
        "required": True,
        "persisted": len(hits) > 0,
        "result_count": len(hits),
        "project_document_count": len(document_ids),
        "project_name": project.get("project_name"),
    }


if __name__ == "__main__":
    raise SystemExit(main())
