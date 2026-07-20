#!/usr/bin/env python3
"""Validation script for US019 proposal review and gap analysis."""

from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.modules.projects.review.sections import review_category_keys
from tests.helpers.pdf import make_text_pdf

BASE_URL = os.environ.get("AI_PRESALES_API_BASE_URL", "http://127.0.0.1:8000")


def main() -> int:
    results: dict[str, object] = {"errors": []}
    client = httpx.Client(base_url=BASE_URL, timeout=600.0)

    create = client.post(
        "/api/v1/projects",
        json={"project_name": "US019 Review Validation", "description": "review e2e"},
    )
    create.raise_for_status()
    project_id = create.json()["project_id"]
    results["project_id"] = project_id

    for filename, text in (
        ("RFP.pdf", "CRM RFP integrations security availability timeline team requirements."),
        ("Appendix-A.pdf", "Appendix commercial pricing licensing assumptions dependencies."),
    ):
        upload = client.post(
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
        )
        upload.raise_for_status()

    proposal = client.post(f"/api/v1/projects/{project_id}/proposal", json={"top_k": 6})
    if proposal.status_code != 200:
        results["errors"].append(f"proposal generation failed: {proposal.status_code}")
        _write_results(results)
        return 1

    generate = client.post(f"/api/v1/projects/{project_id}/review", json={"top_k": 6})
    generate.raise_for_status()
    review = generate.json()["review"]
    results["category_count"] = len(review.get("categories", []))
    results["expected_category_count"] = len(review_category_keys())
    if results["category_count"] != results["expected_category_count"]:
        results["errors"].append("review missing categories")

    metrics = review.get("metrics") or {}
    results["coverage_score_exists"] = "coverage_percent" in metrics and metrics["coverage_percent"] >= 0
    if not results["coverage_score_exists"]:
        results["errors"].append("coverage score missing")

    findings = [
        finding
        for category in review.get("categories", [])
        for finding in category.get("findings") or []
    ]
    results["findings_count"] = len(findings)
    if not findings:
        results["errors"].append("no findings generated")

    without_severity = [f.get("title") for f in findings if not f.get("severity")]
    results["findings_without_severity"] = without_severity
    if without_severity:
        results["errors"].append("findings missing severity")

    without_citations = [
        f.get("title")
        for f in findings
        if "citations" not in f or not f.get("citations")
    ]
    results["findings_without_citations"] = without_citations
    if len(without_citations) == len(findings) and findings:
        results["errors"].append("no findings include citations")

    markdown = client.get(
        f"/api/v1/projects/{project_id}/review/export",
        params={"format": "markdown"},
    )
    results["markdown_export_ok"] = markdown.status_code == 200 and "Coverage" in markdown.text
    if not results["markdown_export_ok"]:
        results["errors"].append("markdown export failed")

    _write_results(results)
    print(json.dumps(results, indent=2))
    return 0 if not results["errors"] else 1


def _write_results(results: dict[str, object]) -> None:
    out_path = ROOT / "docs" / "validation-us019-review.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("WROTE", out_path)


if __name__ == "__main__":
    raise SystemExit(main())
