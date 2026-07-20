#!/usr/bin/env python3
"""Validation script for US018 AI proposal generator."""

from __future__ import annotations

import json
import os
import sys
from io import BytesIO
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.modules.projects.proposal.sections import proposal_section_keys
from tests.helpers.pdf import make_text_pdf

BASE_URL = os.environ.get("AI_PRESALES_API_BASE_URL", "http://127.0.0.1:8000")


def main() -> int:
    results: dict[str, object] = {"errors": []}
    client = httpx.Client(base_url=BASE_URL, timeout=300.0)

    create = client.post(
        "/api/v1/projects",
        json={"project_name": "US018 Proposal Validation", "description": "proposal e2e"},
    )
    create.raise_for_status()
    project_id = create.json()["project_id"]
    results["project_id"] = project_id

    for filename, text in (
        ("RFP.pdf", "CRM RFP with integrations delivery timeline and team requirements."),
        ("Appendix-A.pdf", "Appendix commercial pricing licensing and assumptions."),
    ):
        upload = client.post(
            f"/api/v1/projects/{project_id}/documents",
            files={"file": (filename, BytesIO(make_text_pdf(text)), "application/pdf")},
        )
        upload.raise_for_status()

    generate = client.post(
        f"/api/v1/projects/{project_id}/proposal",
        json={"top_k": 6},
    )
    generate.raise_for_status()
    proposal = generate.json()["proposal"]
    results["section_count"] = len(proposal.get("sections", []))
    results["expected_section_count"] = len(proposal_section_keys())

    if results["section_count"] != results["expected_section_count"]:
        results["errors"].append("proposal missing sections")

    sections_without_citations = [
        section["key"]
        for section in proposal.get("sections", [])
        if not section.get("citations")
    ]
    results["sections_without_citations"] = sections_without_citations
    if sections_without_citations:
        results["errors"].append("one or more sections missing citations")

    markdown = client.get(
        f"/api/v1/projects/{project_id}/proposal/export",
        params={"format": "markdown"},
    )
    results["markdown_export_ok"] = markdown.status_code == 200 and "Executive Summary" in markdown.text
    if not results["markdown_export_ok"]:
        results["errors"].append("markdown export failed")

    out_path = ROOT / "docs" / "validation-us018-proposal.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    print("WROTE", out_path)
    return 0 if not results["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
