"""Compute aggregate metrics from a review report."""

from app.modules.projects.schemas.review import (
    ReviewCategoryResult,
    ReviewMetrics,
    ReviewReport,
    ReviewSeverity,
)

_SEVERITY_SCORE = {
    ReviewSeverity.low: 1.0,
    ReviewSeverity.medium: 2.0,
    ReviewSeverity.high: 3.0,
    ReviewSeverity.critical: 4.0,
}


def compute_review_metrics(categories: list[ReviewCategoryResult]) -> ReviewMetrics:
    """Derive coverage and readiness metrics from category findings."""
    all_findings = [finding for category in categories for finding in category.findings]

    covered = 0
    partial = 0
    missing = 0
    for finding in all_findings:
        if finding.coverage_status == "covered":
            covered += 1
        elif finding.coverage_status == "partially_covered":
            partial += 1
        elif finding.coverage_status == "missing":
            missing += 1

    coverage_denominator = covered + partial + missing
    if coverage_denominator == 0:
        coverage_percent = 100.0 if not all_findings else 75.0
    else:
        coverage_percent = round(((covered + 0.5 * partial) / coverage_denominator) * 100, 2)

    critical_findings = sum(
        1 for finding in all_findings if finding.severity == ReviewSeverity.critical
    )
    if all_findings:
        average_severity = round(
            sum(_SEVERITY_SCORE[finding.severity] for finding in all_findings)
            / len(all_findings),
            2,
        )
    else:
        average_severity = 1.0

    penalty = min(100.0, critical_findings * 15 + missing * 5 + average_severity * 8)
    readiness_score = round(max(0.0, min(100.0, coverage_percent - penalty * 0.35)), 2)

    return ReviewMetrics(
        coverage_percent=coverage_percent,
        requirements_covered=covered,
        requirements_missing=missing,
        critical_findings=critical_findings,
        average_severity_score=average_severity,
        readiness_score=readiness_score,
    )


def attach_metrics(report: ReviewReport) -> ReviewReport:
    """Recompute and attach metrics to a review report."""
    metrics = compute_review_metrics(report.categories)
    return report.model_copy(update={"metrics": metrics})
