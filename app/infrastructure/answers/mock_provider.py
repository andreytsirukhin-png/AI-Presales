from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.modules.documents.schemas.search import SearchResult

FALLBACK_ANSWER = INSUFFICIENT_CONTEXT_ANSWER


class MockAnswerProvider:
    """Deterministic answer provider for development and tests."""

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        """Build an answer from ranked context chunks.

        Args:
            question: User question to answer.
            context_chunks: Ranked search results used as answer context.

        Returns:
            A deterministic answer derived only from non-empty context text.
        """
        usable_texts = [
            chunk.text.strip()
            for chunk in context_chunks
            if chunk.text.strip()
        ]

        if not usable_texts:
            return FALLBACK_ANSWER

        context_body = " ".join(usable_texts)
        return f"Based on the indexed document: {context_body}"
