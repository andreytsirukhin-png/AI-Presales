"""Parse structured review findings from LLM JSON responses."""

import json
import re

from app.modules.documents.schemas.ask import AnswerCitation
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.services.citations import build_citations
from app.modules.projects.schemas.review import ReviewFinding, ReviewSeverity


def _severity_from_raw(value: str) -> ReviewSeverity:
    normalized = value.strip().lower()
    mapping = {
        "low": ReviewSeverity.low,
        "medium": ReviewSeverity.medium,
        "high": ReviewSeverity.high,
        "critical": ReviewSeverity.critical,
    }
    return mapping.get(normalized, ReviewSeverity.medium)


def _extract_json_payload(raw_text: str) -> dict[str, object]:
    stripped = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", stripped, re.DOTALL)
    if fence_match:
        stripped = fence_match.group(1)
    return json.loads(stripped)


def _citations_for_finding(
    finding_data: dict[str, object],
    default_citations: list[AnswerCitation],
) -> list[AnswerCitation]:
    document = finding_data.get("source_document")
    page = finding_data.get("page")
    if document:
        matched = [
            citation
            for citation in default_citations
            if citation.document == str(document)
            and (page is None or citation.page == int(page))
        ]
        if matched:
            return matched[:3]
    return default_citations[:3]


def parse_category_response(
    raw_text: str,
    *,
    search_results: list[SearchResult],
) -> tuple[str, list[ReviewFinding]]:
    """Parse summary and findings from a category LLM response."""
    default_citations = build_citations(search_results)
    try:
        payload = _extract_json_payload(raw_text)
    except (json.JSONDecodeError, TypeError):
        return raw_text.strip(), _fallback_findings(raw_text, default_citations)

    summary = str(payload.get("summary", "")).strip() or raw_text.strip()[:500]
    findings_raw = payload.get("findings", [])
    if not isinstance(findings_raw, list):
        return summary, _fallback_findings(raw_text, default_citations)

    findings: list[ReviewFinding] = []
    for item in findings_raw:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "Finding")).strip()
        description = str(item.get("description", "")).strip() or title
        recommendation = str(item.get("recommendation", "Review and update the proposal.")).strip()
        coverage_raw = item.get("coverage_status")
        coverage_status = (
            str(coverage_raw).lower()
            if coverage_raw in {"covered", "partially_covered", "missing"}
            else None
        )
        page_raw = item.get("page")
        page_number = int(page_raw) if page_raw is not None else None
        findings.append(
            ReviewFinding(
                title=title,
                description=description,
                severity=_severity_from_raw(str(item.get("severity", "medium"))),
                recommendation=recommendation,
                coverage_status=coverage_status,  # type: ignore[arg-type]
                proposal_section=str(item["proposal_section"])
                if item.get("proposal_section")
                else None,
                source_document=str(item["source_document"])
                if item.get("source_document")
                else None,
                page=page_number,
                citations=_citations_for_finding(item, default_citations),
            )
        )

    if not findings:
        findings = _fallback_findings(raw_text, default_citations)
    return summary, findings


def _fallback_findings(
    raw_text: str,
    citations: list[AnswerCitation],
) -> list[ReviewFinding]:
    """Create a single medium finding when structured parsing is unavailable."""
    snippet = raw_text.strip()[:400] or "Review output could not be structured."
    primary = citations[0] if citations else None
    return [
        ReviewFinding(
            title="Review note",
            description=snippet,
            severity=ReviewSeverity.medium,
            recommendation="Review this item against source documents and update the proposal.",
            source_document=primary.document if primary else None,
            page=primary.page if primary else None,
            citations=citations[:3],
        )
    ]
