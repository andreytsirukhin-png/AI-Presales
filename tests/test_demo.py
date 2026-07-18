from app.services.demo_analysis import build_demo_analysis


def test_demo_analysis_has_traceability() -> None:
    result = build_demo_analysis()
    assert result.requirements
    assert result.requirements[0].evidence
    assert 0 <= result.confidence <= 1
