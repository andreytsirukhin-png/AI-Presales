"""Shared prompt construction for context-only answer providers."""

from app.modules.documents.schemas.search import SearchResult

SYSTEM_INSTRUCTION = (
    "You answer questions using only the supplied document context. "
    "Do not use external knowledge. "
    "When the context includes page numbers, reference those pages in your answer when citing facts. "
    "If the answer cannot be found in the context, clearly state that the document "
    "does not contain enough information. "
    "Do not invent facts, page numbers, or citations."
)


def _format_source_block(chunk: SearchResult) -> str:
    """Format one retrieved chunk with human-readable source metadata."""
    chunk_text = chunk.text.strip()
    if not chunk_text:
        return ""

    metadata = chunk.metadata
    if metadata is None:
        return f"[Chunk {chunk.chunk_index}]\n{chunk_text}"

    page_line = (
        f"Page:\n{metadata.page_number}\n\n"
        if metadata.page_number is not None
        else ""
    )
    section_line = (
        f"Section:\n{metadata.section}\n\n"
        if metadata.section
        else ""
    )
    heading_line = (
        f"Heading:\n{metadata.heading}\n\n"
        if metadata.heading
        else ""
    )
    project_line = (
        f"Project:\n{metadata.project_name}\n\n"
        if metadata.project_name
        else ""
    )

    return (
        "Source\n"
        f"Document:\n{metadata.document_name}\n\n"
        f"{project_line}"
        f"{page_line}"
        f"Chunk:\n{metadata.chunk_index}\n\n"
        f"{section_line}"
        f"{heading_line}"
        f"Content:\n{chunk_text}"
    )


def build_answer_prompt(question: str, context_chunks: list[SearchResult]) -> str:
    """Build a deterministic user prompt from a question and retrieved chunks."""
    context_sections = [
        block
        for block in (_format_source_block(chunk) for chunk in context_chunks)
        if block
    ]
    context_body = "\n\n---\n\n".join(context_sections)
    return (
        f"Question:\n{question.strip()}\n\n"
        "Document Context:\n"
        f"{context_body}"
    )
