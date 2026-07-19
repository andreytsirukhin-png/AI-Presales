#!/usr/bin/env python3
"""End-to-end validation script for Ollama embedding integration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.helpers.pdf import make_text_pdf
from ui.prompts import ANALYSIS_LABELS, get_analysis_prompt

BASE_URL = "http://127.0.0.1:8000"
SAMPLE_PDF = ROOT / "data" / "20980ba6-8b0e-4b0e-ad34-9016a85fe4ac.pdf"
SEARCH_QUERIES = [
    "CRM integration requirements",
    "project delivery timeline and phases",
    "security and compliance requirements",
]


def main() -> int:
    results: dict[str, object] = {"errors": []}
    client = httpx.Client(base_url=BASE_URL, timeout=180.0)

    status = client.get("/api/v1/status").json()
    results["status"] = status
    print("STATUS", json.dumps(status, indent=2))

    pdf_path = SAMPLE_PDF if SAMPLE_PDF.exists() else None
    if pdf_path is None:
        pdf_bytes = make_text_pdf(
            "RFP for CRM System. Integration with SAP required. "
            "Delivery must complete within 12 months. Security: SOC2 compliance mandatory. "
            "Budget cap is 500000 USD. Risks include data migration complexity."
        )
        filename = "validation-rfp.pdf"
    else:
        pdf_bytes = pdf_path.read_bytes()
        filename = pdf_path.name

    upload = client.post(
        "/api/v1/documents/upload",
        files={"file": (filename, pdf_bytes, "application/pdf")},
    )
    upload.raise_for_status()
    document_id = upload.json()["document_id"]
    results["document_id"] = document_id
    print("UPLOAD", document_id)

    for step in ("parse", "chunks", "embeddings", "index"):
        response = client.post(f"/api/v1/documents/{document_id}/{step}")
        response.raise_for_status()
        payload = response.json()
        results[step] = payload
        print(step.upper(), json.dumps(payload)[:200])

    embed_payload = results["embeddings"]
    assert embed_payload["embedding_dimension"] == 768
    assert embed_payload["chunk_count"] > 0
    assert results["index"]["chunks_indexed"] == embed_payload["chunk_count"]

    search_results: dict[str, object] = {}
    for query in SEARCH_QUERIES:
        response = client.post(
            f"/api/v1/documents/{document_id}/search",
            json={"query": query, "top_k": 5},
        )
        response.raise_for_status()
        payload = response.json()
        search_results[query] = {
            "result_count": payload["result_count"],
            "top_score": payload["results"][0]["score"] if payload["results"] else None,
            "top_preview": payload["results"][0]["text"][:120] if payload["results"] else None,
        }
    results["search"] = search_results
    print("SEARCH", json.dumps(search_results, indent=2))

    analyses: dict[str, object] = {}
    for label in ANALYSIS_LABELS:
        prompt = get_analysis_prompt(label)
        response = client.post(
            f"/api/v1/documents/{document_id}/ask",
            json={"question": prompt, "top_k": 10},
        )
        if response.status_code >= 400:
            analyses[label] = {"error": response.text}
            results["errors"].append(f"{label}: HTTP {response.status_code}")
        else:
            payload = response.json()
            analyses[label] = {
                "status": payload["status"],
                "answer_length": len(payload.get("answer", "")),
                "source_count": len(payload.get("sources", [])),
                "answer_preview": payload.get("answer", "")[:160],
            }
        print("ANALYSIS", label, analyses[label].get("status", analyses[label].get("error")))

    results["analyses"] = analyses

    comparison = compare_mock_vs_ollama(pdf_bytes)
    results["mock_vs_ollama"] = comparison
    print("COMPARISON", json.dumps(comparison, indent=2))

    out_path = ROOT / "docs" / "validation-us014-ollama.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("WROTE", out_path)
    return 0 if not results["errors"] else 1


def compare_mock_vs_ollama(pdf_bytes: bytes) -> dict[str, object]:
    """Compare retrieval quality between mock and Ollama embeddings."""
    from app.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
    from app.infrastructure.embeddings.ollama_provider import OllamaEmbeddingProvider
    from app.infrastructure.vector_store.in_memory_store import InMemoryVectorStore
    from app.modules.documents.chunkers.text_chunker import TextChunker
    from app.modules.documents.parsers.pdf_parser import PDFParser
    from app.modules.documents.schemas.index import IndexedChunk

    parser = PDFParser()
    chunker = TextChunker()
    parsed = parser.parse(pdf_bytes)
    chunks = chunker.chunk(parsed.text)
    chunk_texts = [chunk.text for chunk in chunks]

    mock_provider = MockEmbeddingProvider(dimension=16)
    ollama_provider = OllamaEmbeddingProvider(dimension=768)
    mock_vectors = mock_provider.embed_texts(chunk_texts)
    ollama_vectors = ollama_provider.embed_texts(chunk_texts)

    mock_store = InMemoryVectorStore()
    ollama_store = InMemoryVectorStore()
    mock_store.upsert(
        "mock-doc",
        [
            IndexedChunk(index=chunk.index, text=chunk.text, vector=vector)
            for chunk, vector in zip(chunks, mock_vectors)
        ],
    )
    ollama_store.upsert(
        "ollama-doc",
        [
            IndexedChunk(index=chunk.index, text=chunk.text, vector=vector)
            for chunk, vector in zip(chunks, ollama_vectors)
        ],
    )

    query = "SAP integration and CRM requirements"
    mock_query = mock_provider.embed(query)
    ollama_query = ollama_provider.embed(query)

    mock_hits = mock_store.search("mock-doc", mock_query, top_k=3)
    ollama_hits = ollama_store.search("ollama-doc", ollama_query, top_k=3)

    return {
        "query": query,
        "chunk_count": len(chunks),
        "mock_top_scores": [round(hit.score, 4) for hit in mock_hits],
        "ollama_top_scores": [round(hit.score, 4) for hit in ollama_hits],
        "mock_top_previews": [hit.text[:100] for hit in mock_hits],
        "ollama_top_previews": [hit.text[:100] for hit in ollama_hits],
        "notes": [
            "Mock vectors are hash-derived and not semantically aligned with queries.",
            "Ollama vectors should rank integration-related chunks higher for integration queries.",
        ],
    }


if __name__ == "__main__":
    raise SystemExit(main())
