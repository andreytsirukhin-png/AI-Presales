import json

import pytest

from app.modules.documents.schemas.ask import AnswerCitation
from app.modules.documents.schemas.search import SearchResult
from app.modules.projects.schemas.review import ReviewSeverity
from app.modules.projects.services.review_parser import parse_category_response


def test_parse_category_response_parses_json_findings() -> None:
    raw = json.dumps(
        {
            "summary": "Coverage is incomplete.",
            "findings": [
                {
                    "title": "Missing ERP integration",
                    "description": "Proposal omits ERP integration detail.",
                    "severity": "high",
                    "recommendation": "Expand Integrations section.",
                    "coverage_status": "missing",
                    "proposal_section": "Integrations",
                    "source_document": "RFP.pdf",
                    "page": 6,
                }
            ],
        }
    )
    results = [
        SearchResult(
            chunk_index=0,
            text="ERP integration required",
            score=0.9,
            metadata=None,
        )
    ]
    summary, findings = parse_category_response(raw, search_results=results)
    assert summary == "Coverage is incomplete."
    assert len(findings) == 1
    assert findings[0].severity == ReviewSeverity.high
    assert findings[0].coverage_status == "missing"


def test_parse_category_response_fallback_creates_finding_with_citations() -> None:
    citations = [
        AnswerCitation(document="RFP.pdf", page=2, score=0.8, chunk_index=0, chunk_id="c0")
    ]
    results = [
        SearchResult(chunk_index=0, text="context", score=0.8, metadata=None),
    ]
    _, findings = parse_category_response("Unstructured review note", search_results=results)
    assert findings
    assert findings[0].severity == ReviewSeverity.medium
