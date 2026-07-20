"""Streamlit demo UI for the AI RFP Analyzer."""

from __future__ import annotations

import streamlit as st

from ui.analysis_handlers import (
    analysis_button_key,
    run_analysis_for_label,
)
from ui.api_client import (
    ApiClientError,
    BackendUnavailableError,
    ask_project,
    check_health,
    create_project,
    delete_project_document,
    get_platform_status,
    get_project_statistics,
    list_project_documents,
    list_projects,
    upload_project_document,
)
from ui.config import UiSettings, apply_backend_status, get_ui_settings
from ui.proposal_view import render_proposal_page
from ui.prompts import ANALYSIS_LABELS


def _init_session_state() -> None:
    defaults = {
        "project_id": None,
        "project_name": None,
        "project_stats": None,
        "project_documents": [],
        "analysis_results": {},
        "analysis_errors": {},
        "last_question": "",
        "last_answer": None,
        "proposal": None,
        "ui_page": "Workspace",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_sources(sources: list[dict[str, object]]) -> None:
    if not sources:
        st.info("No supporting source chunks were returned.")
        return

    st.markdown("**Sources**")
    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        document_name = metadata.get("document_name") or "document"
        page_number = metadata.get("page_number")
        chunk_index = source.get("chunk_index", metadata.get("chunk_index", "?"))
        score = source.get("score", 0.0)
        text = str(source.get("text", "")).strip()
        page_label = f"Page {page_number}" if page_number is not None else "Page n/a"
        title = (
            f"Source {index} · {document_name} · {page_label} · "
            f"Chunk {chunk_index} · Score {float(score):.3f}"
        )
        with st.expander(title, expanded=False):
            st.write(text)


def _refresh_project_state(settings: UiSettings, project_id: str) -> None:
    st.session_state.project_stats = get_project_statistics(
        settings.api_base_url,
        project_id,
        timeout=settings.request_timeout_seconds,
    )
    documents_payload = list_project_documents(
        settings.api_base_url,
        project_id,
        timeout=settings.request_timeout_seconds,
    )
    st.session_state.project_documents = documents_payload.get("documents", [])


def _render_sidebar(settings: UiSettings) -> None:
    st.sidebar.header("Project Workspace")
    st.sidebar.write(f"Backend URL: `{settings.api_base_url}`")

    display_settings = settings
    try:
        check_health(settings.api_base_url, timeout=5.0)
        display_settings = apply_backend_status(
            settings,
            get_platform_status(settings.api_base_url, timeout=5.0),
        )
        st.sidebar.success("Backend connected")
    except BackendUnavailableError:
        st.sidebar.error("Backend unavailable. Start FastAPI on port 8000.")
        return
    except ApiClientError as exc:
        st.sidebar.error(str(exc))
        return

    with st.sidebar.form("create_project_form"):
        new_name = st.text_input("New project name", value="RFP Workspace")
        new_description = st.text_area("Description", value="")
        if st.form_submit_button("Create Project"):
            try:
                created = create_project(
                    settings.api_base_url,
                    project_name=new_name.strip(),
                    description=new_description.strip(),
                    timeout=settings.request_timeout_seconds,
                )
            except (BackendUnavailableError, ApiClientError) as exc:
                st.sidebar.error(str(exc))
            else:
                st.session_state.project_id = created["project_id"]
                st.session_state.project_name = created["project_name"]
                st.session_state.analysis_results = {}
                st.session_state.analysis_errors = {}
                st.session_state.last_answer = None
                _refresh_project_state(settings, created["project_id"])

    try:
        projects_payload = list_projects(settings.api_base_url, timeout=5.0)
    except (BackendUnavailableError, ApiClientError):
        projects_payload = {"projects": []}

    project_options = {
        project["project_name"]: project["project_id"]
        for project in projects_payload.get("projects", [])
    }
    if project_options:
        selected_name = st.sidebar.selectbox(
            "Switch Project",
            options=list(project_options.keys()),
            index=(
                list(project_options.values()).index(st.session_state.project_id)
                if st.session_state.project_id in project_options.values()
                else 0
            ),
        )
        selected_id = project_options[selected_name]
        if selected_id != st.session_state.project_id:
            st.session_state.project_id = selected_id
            st.session_state.project_name = selected_name
            st.session_state.analysis_results = {}
            st.session_state.analysis_errors = {}
            st.session_state.last_answer = None
        if st.session_state.project_id:
            _refresh_project_state(settings, st.session_state.project_id)

    st.sidebar.divider()
    page = st.sidebar.radio("Navigation", ["Workspace", "Proposal"], key="ui_page")
    st.session_state.ui_page = page

    st.sidebar.divider()
    st.sidebar.write(f"Current project: **{st.session_state.project_name or 'None'}**")
    stats = st.session_state.project_stats or {}
    st.sidebar.write(f"Documents: {stats.get('document_count', 0)}")
    st.sidebar.write(f"Indexed chunks: {stats.get('indexed_chunks', 0)}")
    st.sidebar.write(f"Embedding model: `{stats.get('embedding_model', display_settings.embedding_provider)}`")
    st.sidebar.write(f"Vector store: `{stats.get('vector_store', display_settings.vector_store)}`")
    if stats.get("last_indexed_at"):
        st.sidebar.write(f"Last indexed: {stats['last_indexed_at']}")

    documents = st.session_state.project_documents or []
    if documents:
        st.sidebar.markdown("**Project documents**")
        for document in documents:
            cols = st.sidebar.columns([3, 1])
            cols[0].write(document.get("filename", document.get("document_id")))
            if cols[1].button("Del", key=f"del_{document['document_id']}"):
                try:
                    delete_project_document(
                        settings.api_base_url,
                        st.session_state.project_id,
                        document["document_id"],
                        timeout=settings.request_timeout_seconds,
                    )
                except (BackendUnavailableError, ApiClientError) as exc:
                    st.sidebar.error(str(exc))
                else:
                    _refresh_project_state(settings, st.session_state.project_id)


def _render_analysis_section(settings: UiSettings, project_id: str) -> None:
    st.header("Step 2 — Analyze Project")
    st.write("Run presales analyses across all indexed documents in the current project.")

    analysis_top_k = st.slider(
        "Analysis top_k",
        min_value=1,
        max_value=20,
        value=10,
        key="analysis_top_k",
    )
    action_cols = st.columns(3)

    for index, label in enumerate(ANALYSIS_LABELS):
        column = action_cols[index % 3]
        with column:
            if st.button(
                label,
                key=analysis_button_key(label),
                use_container_width=True,
                disabled=not project_id,
            ):
                with st.spinner(f"Running {label}..."):
                    results, errors = run_analysis_for_label(
                        label=label,
                        results=dict(st.session_state.analysis_results),
                        errors=dict(st.session_state.analysis_errors),
                        base_url=settings.api_base_url,
                        project_id=project_id,
                        top_k=analysis_top_k,
                        timeout=settings.request_timeout_seconds,
                    )
                st.session_state.analysis_results = results
                st.session_state.analysis_errors = errors

    for label in ANALYSIS_LABELS:
        if label in st.session_state.analysis_errors:
            st.error(f"{label}: {st.session_state.analysis_errors[label]}")

    completed_labels = [
        label for label in ANALYSIS_LABELS if label in st.session_state.analysis_results
    ]
    if completed_labels:
        st.subheader("Analysis Results")
        for label in completed_labels:
            payload = st.session_state.analysis_results[label]
            with st.expander(label, expanded=False):
                st.markdown(payload.get("answer", ""))
                _render_sources(payload.get("sources", []))


def main() -> None:
    """Render the Streamlit demo application."""
    settings = get_ui_settings()
    _init_session_state()

    st.set_page_config(page_title="AI RFP Analyzer", page_icon="📄", layout="wide")
    st.title("AI RFP Analyzer")
    st.caption("Project workspace for multi-document RFP analysis, search, and Q&A.")

    _render_sidebar(settings)

    if st.session_state.get("ui_page") == "Proposal":
        render_proposal_page(settings)
        return

    project_id = st.session_state.project_id
    if not project_id:
        st.info("Create or select a project in the sidebar to begin.")
        return

    st.header("Step 1 — Upload Document to Project")
    uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if uploaded_file is not None and st.button("Upload & Index", type="primary"):
        try:
            with st.spinner("Uploading and indexing..."):
                upload_project_document(
                    settings.api_base_url,
                    project_id,
                    filename=uploaded_file.name,
                    content=uploaded_file.getvalue(),
                    timeout=settings.request_timeout_seconds,
                )
        except (BackendUnavailableError, ApiClientError) as exc:
            st.error(str(exc))
        else:
            _refresh_project_state(settings, project_id)
            st.success(f"Indexed `{uploaded_file.name}` in the current project.")
            st.session_state.analysis_results = {}
            st.session_state.analysis_errors = {}
            st.session_state.last_answer = None

    stats = st.session_state.project_stats or {}
    if stats.get("document_count", 0) == 0:
        st.info("Upload at least one PDF to unlock analysis and Q&A.")
        return

    _render_analysis_section(settings, project_id)

    st.header("Step 3 — Ask the Project")
    question = st.text_area("Question", value=st.session_state.last_question, height=100)
    ask_top_k = st.slider("Ask top_k", min_value=1, max_value=20, value=5, key="ask_top_k")

    if st.button("Ask", type="primary", disabled=not question.strip()):
        try:
            with st.spinner("Generating answer..."):
                response = ask_project(
                    settings.api_base_url,
                    project_id,
                    question=question.strip(),
                    top_k=ask_top_k,
                    timeout=settings.request_timeout_seconds,
                )
        except (BackendUnavailableError, ApiClientError) as exc:
            st.error(str(exc))
        else:
            st.session_state.last_question = question.strip()
            st.session_state.last_answer = response
            st.markdown("### Answer")
            st.write(response.get("answer", ""))
            _render_sources(response.get("sources", []))

    if st.session_state.last_answer and not question.strip():
        st.markdown("### Answer")
        st.write(st.session_state.last_answer.get("answer", ""))
        _render_sources(st.session_state.last_answer.get("sources", []))


if __name__ == "__main__":
    main()
