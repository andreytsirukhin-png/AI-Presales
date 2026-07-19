from app.modules.documents.schemas.search import SearchResult


def has_usable_context(context_chunks: list[SearchResult]) -> bool:
    """Return True when at least one retrieved chunk contains non-empty text."""
    return any(chunk.text.strip() for chunk in context_chunks)
