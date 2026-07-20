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
    ask_question,
    check_health,
    get_platform_status,
    process_document,
)
from ui.config import UiSettings, apply_backend_status, get_ui_settings
from ui.prompts import ANALYSIS_LABELS


def _init_session_state() -> None:
    defaults = {
        "document_id": None,
        "filename": None,
        "file_size": None,
        "chunk_count": None,
        "processing_status": "Not started",
        "analysis_results": {},
        "analysis_errors": {},
        "last_question": "",
        "last_answer": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _format_bytes(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "Unknown"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _render_sources(sources: list[dict[str, object]]) -> None:
    if not sources:
        st.info("No supporting source chunks were returned.")
        return

    for index, source in enumerate(sources, start=1):
        chunk_index = source.get("chunk_index", "?")
        score = source.get("score", 0.0)
        text = str(source.get("text", "")).strip()
        preview = text if len(text) <= 500 else f"{text[:500]}..."
        with st.expander(f"Source {index} · Chunk {chunk_index} · Score {score:.3f}"):
            st.write(preview)


def _render_sidebar(settings: UiSettings) -> None:
    st.sidebar.header("Session")
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
    except ApiClientError as exc:
        st.sidebar.error(str(exc))

    st.sidebar.divider()
    st.sidebar.write(f"Document name: {st.session_state.filename or 'None'}")
    st.sidebar.write(f"Document ID: `{st.session_state.document_id or 'None'}`")
    st.sidebar.write(f"Status: **{st.session_state.processing_status}**")
    st.sidebar.write(f"Embedding provider: `{display_settings.embedding_provider}`")
    st.sidebar.write(f"Answer provider: `{display_settings.answer_provider}`")
    st.sidebar.write(f"Answer model: `{display_settings.answer_model}`")
    st.sidebar.write(f"Vector store: `{display_settings.vector_store}`")
    if st.session_state.chunk_count is not None:
        st.sidebar.write(f"Chunk count: {st.session_state.chunk_count}")


def _render_analysis_section(settings: UiSettings, document_id: str) -> None:
    st.header("Step 2 — Analyze")
    st.write("Run specialized presales analyses using the existing ask endpoint.")

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
                disabled=not document_id,
            ):
                with st.spinner(f"Running {label}..."):
                    results, errors = run_analysis_for_label(
                        label=label,
                        results=dict(st.session_state.analysis_results),
                        errors=dict(st.session_state.analysis_errors),
                        base_url=settings.api_base_url,
                        document_id=document_id,
                        top_k=analysis_top_k,
                        timeout=settings.request_timeout_seconds,
                    )
                st.session_state.analysis_results = results
                st.session_state.analysis_errors = errors
                if label in errors:
                    st.error(f"{label} failed: {errors[label]}")

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
    st.caption(
        "Analyze requirements, risks, assumptions, clarification questions, "
        "and delivery implications from RFP documents."
    )

    _render_sidebar(settings)

    st.header("Step 1 — Upload RFP")
    uploaded_file = st.file_uploader("Upload an RFP PDF", type=["pdf"])

    if uploaded_file is not None:
        st.write(f"Selected file: `{uploaded_file.name}`")
        st.write(f"File size: {_format_bytes(uploaded_file.size)}")

    if st.button("Process Document", type="primary", disabled=uploaded_file is None):
        assert uploaded_file is not None
        progress = st.progress(0.0, text="Starting...")
        stage_labels: list[str] = []

        def update_progress(stage: str) -> None:
            stage_labels.append(stage)
            st.session_state.processing_status = stage
            progress.progress(min(len(stage_labels) / 6, 1.0), text=stage)

        try:
            result = process_document(
                settings.api_base_url,
                filename=uploaded_file.name,
                content=uploaded_file.getvalue(),
                timeout=settings.request_timeout_seconds,
                progress_callback=update_progress,
            )
        except BackendUnavailableError as exc:
            st.error(str(exc))
        except ApiClientError as exc:
            if exc.status_code == 415:
                st.error("Unsupported file type. Upload a PDF document.")
            elif exc.status_code == 413:
                st.error("Upload failed because the file is too large.")
            elif exc.status_code == 422:
                st.error(f"Document processing failed: {exc}")
            else:
                st.error(f"Document processing failed: {exc}")
        else:
            st.session_state.document_id = result.document_id
            st.session_state.filename = result.filename
            st.session_state.file_size = result.size_bytes
            st.session_state.chunk_count = result.chunk_count
            st.session_state.processing_status = "Ready."
            st.session_state.analysis_results = {}
            st.session_state.analysis_errors = {}
            st.session_state.last_answer = None
            progress.progress(1.0, text="Ready.")
            st.success(
                f"Document processed successfully. Indexed {result.chunks_indexed} chunks."
            )

    document_id = st.session_state.document_id
    if not document_id:
        st.info("Upload and process an RFP to unlock analysis and Q&A.")
        return

    _render_analysis_section(settings, document_id)

    st.header("Step 3 — Ask the RFP")
    question = st.text_area("Question", value=st.session_state.last_question, height=100)
    ask_top_k = st.slider("Ask top_k", min_value=1, max_value=20, value=5, key="ask_top_k")

    if st.button("Ask", type="primary", disabled=not question.strip()):
        try:
            with st.spinner("Generating answer..."):
                response = ask_question(
                    settings.api_base_url,
                    document_id,
                    question=question.strip(),
                    top_k=ask_top_k,
                    timeout=settings.request_timeout_seconds,
                )
        except BackendUnavailableError as exc:
            st.error(str(exc))
        except ApiClientError as exc:
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
