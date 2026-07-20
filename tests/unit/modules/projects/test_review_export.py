from datetime import UTC, datetime

from app.modules.projects.schemas.review import (
    ReviewCategoryResult,
    ReviewFinding,
    ReviewMetrics,
    ReviewReport,
    ReviewSeverity,
)
from app.modules.projects.services.review_export import review_to_docx_bytes, review_to_markdown


def _sample_review() -> ReviewReport:
    generated_at = datetime.now(UTC)
    finding = ReviewFinding(
        title="Missing integration",
        description="ERP integration is not described.",
        severity=ReviewSeverity.high,
        recommendation="Expand the Integrations section.",
        coverage_status="missing",
        proposal_section="Integrations",
        citations=[],
    )
    category = ReviewCategoryResult(
        key="missing_requirements",
        title="Missing Requirements",
        summary="Several gaps identified.",
        findings=[finding],
        generated_at=generated_at,
        status="generated",
    )
    metrics = ReviewMetrics(
        coverage_percent=72.5,
        requirements_covered=3,
        requirements_missing=1,
        critical_findings=0,
        average_severity_score=2.5,
        readiness_score=68.0,
    )
    return ReviewReport(
        project_id="p1",
        project_name="Demo",
        generated_at=generated_at,
        metrics=metrics,
        categories=[category],
    )


def test_review_to_markdown_includes_metrics_and_finding() -> None:
    markdown = review_to_markdown(_sample_review())
    assert "Coverage" in markdown
    assert "Missing integration" in markdown


def test_review_to_docx_bytes_is_non_empty() -> None:
    docx_bytes = review_to_docx_bytes(_sample_review())
    assert docx_bytes.startswith(b"PK")
