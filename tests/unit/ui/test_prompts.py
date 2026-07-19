from ui.prompts import ANALYSIS_LABELS, ANALYSIS_PROMPTS


def test_analysis_prompts_are_deterministic() -> None:
    assert ANALYSIS_PROMPTS["Requirements"] == (
        "Extract all functional and non-functional requirements from this RFP."
    )
    assert ANALYSIS_PROMPTS["Delivery Phases"] == (
        "Propose a high-level delivery plan based on this RFP."
    )


def test_analysis_labels_are_in_display_order() -> None:
    assert ANALYSIS_LABELS[0] == "Executive Summary"
    assert ANALYSIS_LABELS[-1] == "Delivery Phases"
    assert len(ANALYSIS_LABELS) == 7


def test_analysis_prompts_cover_all_demo_actions() -> None:
    expected_labels = {
        "Executive Summary",
        "Requirements",
        "Risks",
        "Clarification Questions",
        "Assumptions",
        "Cost Drivers",
        "Delivery Phases",
    }

    assert set(ANALYSIS_PROMPTS) == expected_labels
