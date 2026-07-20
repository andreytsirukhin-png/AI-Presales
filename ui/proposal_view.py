"""Streamlit proposal workspace page."""

from __future__ import annotations

import streamlit as st

from ui.api_client import (
    ApiClientError,
    BackendUnavailableError,
    export_project_proposal,
    generate_project_proposal,
    get_project_proposal,
    regenerate_project_proposal_sections,
)
from ui.config import UiSettings


def _render_section_citations(section: dict[str, object]) -> None:
    citations = section.get("citations") or []
    if not citations:
        return
    st.caption(
        ", ".join(
            f"{citation.get('document')} p.{citation.get('page')}"
            if citation.get("page")
            else str(citation.get("document"))
            for citation in citations
        )
    )


def render_proposal_page(settings: UiSettings) -> None:
    """Render proposal generation, regeneration, and export controls."""
    st.header("Proposal Generator")
    project_id = st.session_state.get("project_id")
    if not project_id:
        st.info("Select a project in the sidebar to generate a proposal.")
        return

    top_k = st.slider("Retrieval top_k per section", 1, 20, 8, key="proposal_top_k")

    if st.button("Generate Proposal", type="primary"):
        try:
            with st.spinner("Generating all proposal sections..."):
                payload = generate_project_proposal(
                    settings.api_base_url,
                    project_id,
                    top_k=top_k,
                    timeout=max(settings.request_timeout_seconds, 300.0),
                )
        except (BackendUnavailableError, ApiClientError) as exc:
            st.error(str(exc))
        else:
            st.session_state.proposal = payload.get("proposal")
            st.success("Proposal generated.")

    proposal = st.session_state.get("proposal")
    if proposal is None:
        try:
            proposal = get_project_proposal(
                settings.api_base_url,
                project_id,
                timeout=settings.request_timeout_seconds,
            ).get("proposal")
            st.session_state.proposal = proposal
        except (BackendUnavailableError, ApiClientError):
            proposal = None

    if not proposal:
        st.info("No cached proposal yet. Click Generate Proposal.")
        return

    sections = proposal.get("sections", [])
    section_options = {section["title"]: section["key"] for section in sections}
    selected_title = st.selectbox("Regenerate section", options=list(section_options.keys()))
    if st.button("Regenerate Selected Section"):
        try:
            with st.spinner(f"Regenerating {selected_title}..."):
                payload = regenerate_project_proposal_sections(
                    settings.api_base_url,
                    project_id,
                    section_keys=[section_options[selected_title]],
                    top_k=top_k,
                    timeout=max(settings.request_timeout_seconds, 120.0),
                )
        except (BackendUnavailableError, ApiClientError) as exc:
            st.error(str(exc))
        else:
            st.session_state.proposal = payload.get("proposal")
            st.success(f"Regenerated {selected_title}.")

    markdown_export = export_project_proposal(
        settings.api_base_url,
        project_id,
        export_format="markdown",
        timeout=settings.request_timeout_seconds,
    )
    st.download_button(
        "Export Markdown",
        data=markdown_export,
        file_name=f"{project_id}-proposal.md",
        mime="text/markdown",
    )
    docx_export = export_project_proposal(
        settings.api_base_url,
        project_id,
        export_format="docx",
        timeout=settings.request_timeout_seconds,
    )
    st.download_button(
        "Export DOCX",
        data=docx_export,
        file_name=f"{project_id}-proposal.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    st.divider()
    for section in st.session_state.proposal.get("sections", []):
        with st.expander(section.get("title", "Section"), expanded=False):
            st.markdown(section.get("content", ""))
            _render_section_citations(section)
            if st.button("Copy section", key=f"copy_{section.get('key')}"):
                st.code(section.get("content", ""))
