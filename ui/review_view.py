"""Streamlit proposal review page."""

from __future__ import annotations

import streamlit as st

from ui.api_client import (
    ApiClientError,
    BackendUnavailableError,
    export_project_review,
    generate_project_review,
    get_project_review,
    regenerate_project_review_categories,
)
from ui.config import UiSettings

_SEVERITY_ORDER = ("critical", "high", "medium", "low")


def _render_finding_citations(finding: dict[str, object]) -> None:
    citations = finding.get("citations") or []
    if not citations:
        if finding.get("source_document"):
            page = finding.get("page")
            page_suffix = f" p.{page}" if page else ""
            st.caption(f"Source: {finding.get('source_document')}{page_suffix}")
        return
    st.caption(
        ", ".join(
            f"{citation.get('document')} p.{citation.get('page')}"
            if citation.get("page")
            else str(citation.get("document"))
            for citation in citations
        )
    )


def render_review_page(settings: UiSettings) -> None:
    """Render proposal review generation, metrics, and findings."""
    st.header("Proposal Review & Gap Analysis")
    project_id = st.session_state.get("project_id")
    if not project_id:
        st.info("Select a project in the sidebar to review its proposal.")
        return

    top_k = st.slider("Retrieval top_k per category", 1, 20, 8, key="review_top_k")

    if st.button("Generate Review", type="primary"):
        try:
            with st.spinner("Running category reviews (one LLM call per category)..."):
                payload = generate_project_review(
                    settings.api_base_url,
                    project_id,
                    top_k=top_k,
                    timeout=max(settings.request_timeout_seconds, 600.0),
                )
        except (BackendUnavailableError, ApiClientError) as exc:
            st.error(str(exc))
        else:
            st.session_state.review = payload.get("review")
            st.success("Review generated.")

    review = st.session_state.get("review")
    if review is None:
        try:
            review = get_project_review(
                settings.api_base_url,
                project_id,
                timeout=settings.request_timeout_seconds,
            ).get("review")
            st.session_state.review = review
        except (BackendUnavailableError, ApiClientError):
            review = None

    if not review:
        st.info("Generate a proposal first, then run Generate Review.")
        return

    metrics = review.get("metrics") or {}
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Coverage %", f"{metrics.get('coverage_percent', 0):.1f}")
    col2.metric("Readiness", f"{metrics.get('readiness_score', 0):.1f}")
    col3.metric("Missing reqs", metrics.get("requirements_missing", 0))
    col4.metric("Critical", metrics.get("critical_findings", 0))

    categories = review.get("categories") or []
    category_options = {category["title"]: category["key"] for category in categories}
    if category_options:
        selected_title = st.selectbox("Regenerate category", options=list(category_options.keys()))
        if st.button("Regenerate Selected Category"):
            try:
                with st.spinner(f"Regenerating {selected_title}..."):
                    payload = regenerate_project_review_categories(
                        settings.api_base_url,
                        project_id,
                        category_keys=[category_options[selected_title]],
                        top_k=top_k,
                        timeout=max(settings.request_timeout_seconds, 180.0),
                    )
            except (BackendUnavailableError, ApiClientError) as exc:
                st.error(str(exc))
            else:
                st.session_state.review = payload.get("review")
                st.success(f"Regenerated {selected_title}.")

    markdown_export = export_project_review(
        settings.api_base_url,
        project_id,
        export_format="markdown",
        timeout=settings.request_timeout_seconds,
    )
    st.download_button(
        "Export Markdown",
        data=markdown_export,
        file_name=f"{project_id}-review.md",
        mime="text/markdown",
    )
    docx_export = export_project_review(
        settings.api_base_url,
        project_id,
        export_format="docx",
        timeout=settings.request_timeout_seconds,
    )
    st.download_button(
        "Export DOCX",
        data=docx_export,
        file_name=f"{project_id}-review.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    all_findings: list[tuple[str, dict[str, object]]] = []
    for category in categories:
        for finding in category.get("findings") or []:
            all_findings.append((category.get("title", "Category"), finding))

    st.subheader("Findings by severity")
    for severity in _SEVERITY_ORDER:
        grouped = [
            (category_title, finding)
            for category_title, finding in all_findings
            if finding.get("severity") == severity
        ]
        if not grouped:
            continue
        st.markdown(f"**{severity.title()}** ({len(grouped)})")
        for category_title, finding in grouped:
            label = f"{finding.get('title', 'Finding')} — {category_title}"
            with st.expander(label, expanded=severity in {"critical", "high"}):
                st.write(finding.get("description", ""))
                if finding.get("recommendation"):
                    st.markdown(f"**Recommendation:** {finding.get('recommendation')}")
                if finding.get("proposal_section"):
                    st.markdown(f"**Proposal section:** {finding.get('proposal_section')}")
                if finding.get("coverage_status"):
                    st.markdown(f"**Coverage:** {finding.get('coverage_status')}")
                _render_finding_citations(finding)

    missing_categories = [
        category
        for category in categories
        if category.get("key") in {"missing_requirements", "missing_integrations", "missing_nfr"}
    ]
    if missing_categories:
        st.subheader("Missing requirements & gaps")
        for category in missing_categories:
            with st.expander(category.get("title", "Gaps"), expanded=False):
                st.markdown(category.get("summary", ""))
                for finding in category.get("findings") or []:
                    st.markdown(f"- **{finding.get('title')}**: {finding.get('description')}")

    contradiction_category = next(
        (category for category in categories if category.get("key") == "contradictions"),
        None,
    )
    if contradiction_category and contradiction_category.get("findings"):
        st.subheader("Contradictions")
        for finding in contradiction_category.get("findings") or []:
            with st.expander(finding.get("title", "Contradiction"), expanded=False):
                st.write(finding.get("description", ""))
                _render_finding_citations(finding)
