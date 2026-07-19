"""Preset analysis prompts for the Streamlit demo."""

ANALYSIS_LABELS: tuple[str, ...] = (
    "Executive Summary",
    "Requirements",
    "Risks",
    "Clarification Questions",
    "Assumptions",
    "Cost Drivers",
    "Delivery Phases",
)

ANALYSIS_PROMPTS: dict[str, str] = {
    "Executive Summary": "Generate an executive summary of this RFP.",
    "Requirements": (
        "Extract all functional and non-functional requirements from this RFP."
    ),
    "Risks": "Identify delivery and commercial risks described in this RFP.",
    "Clarification Questions": (
        "Generate clarification questions that should be sent to the customer "
        "before estimation."
    ),
    "Assumptions": "Generate proposal assumptions required for estimation.",
    "Cost Drivers": (
        "Identify factors that will significantly increase implementation effort."
    ),
    "Delivery Phases": "Propose a high-level delivery plan based on this RFP.",
}


def get_analysis_prompt(label: str) -> str:
    """Return the preset prompt for an analysis label."""
    return ANALYSIS_PROMPTS[label]
