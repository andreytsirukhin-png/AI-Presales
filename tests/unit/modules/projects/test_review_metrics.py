from datetime import UTC, datetime

from app.modules.projects.schemas.review import (
    ReviewCategoryResult,
    ReviewFinding,
    ReviewMetrics,
    ReviewSeverity,
)
from app.modules.projects.services.review_metrics import compute_review_metrics


def test_compute_review_metrics_counts_coverage_and_critical() -> None:
    categories = [
        ReviewCategoryResult(
            key="coverage_score",
            title="Coverage Score",
            summary="summary",
            findings=[
                ReviewFinding(
                    title="covered item",
                    description="ok",
                    severity=ReviewSeverity.low,
                    recommendation="none",
                    coverage_status="covered",
                ),
                ReviewFinding(
                    title="missing item",
                    description="gap",
                    severity=ReviewSeverity.critical,
                    recommendation="fix",
                    coverage_status="missing",
                ),
            ],
            generated_at=datetime.now(UTC),
            status="generated",
        )
    ]
    metrics = compute_review_metrics(categories)
    assert isinstance(metrics, ReviewMetrics)
    assert metrics.requirements_covered == 1
    assert metrics.requirements_missing == 1
    assert metrics.critical_findings == 1
    assert 0 <= metrics.coverage_percent <= 100
    assert 0 <= metrics.readiness_score <= 100
