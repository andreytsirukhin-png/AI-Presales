from app.models.analysis import (
    AnalysisResult,
    Assumption,
    ClarificationQuestion,
    Evidence,
    Requirement,
    RequirementType,
    Risk,
    Severity,
)


def build_demo_analysis() -> AnalysisResult:
    requirement = Requirement(
        id="REQ-001",
        title="CRM integration",
        description="The solution must retrieve and update customer and deal data in the CRM.",
        type=RequirementType.integration,
        mandatory=True,
        evidence=[
            Evidence(
                quote="The platform shall integrate with the existing CRM.",
                page=4,
                section="Integrations",
            )
        ],
    )

    return AnalysisResult(
        document_summary=(
            "The document describes an enterprise workflow automation solution "
            "with CRM, ERP and document-management integrations."
        ),
        requirements=[requirement],
        clarification_questions=[
            ClarificationQuestion(
                id="Q-001",
                category="Integration",
                question="Which CRM product and version are currently used?",
                rationale="The integration approach and estimate depend on available APIs.",
                priority=Severity.high,
                related_requirement_ids=["REQ-001"],
            )
        ],
        risks=[
            Risk(
                id="RISK-001",
                title="Unconfirmed CRM API availability",
                description="Required endpoints may be unavailable or insufficient.",
                probability=Severity.medium,
                impact=Severity.high,
                mitigation="Validate API documentation and access during Discovery.",
                evidence=requirement.evidence,
            )
        ],
        assumptions=[
            Assumption(
                id="ASM-001",
                statement="The customer will provide documented and supported CRM APIs.",
                validation_needed=True,
                related_requirement_ids=["REQ-001"],
            )
        ],
        confidence=0.83,
    )
