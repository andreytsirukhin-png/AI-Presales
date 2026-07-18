from typing import Protocol

from app.modules.documents.schemas.search import SearchResult


class AnswerProvider(Protocol):
    """Abstraction for generating answers from retrieved context."""

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        """Generate an answer using only the supplied context chunks."""
        ...
