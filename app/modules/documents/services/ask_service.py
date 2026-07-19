from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.infrastructure.answers.protocol import AnswerProvider
from app.modules.documents.schemas.ask import AnswerSource, AskRequest, AskResponse
from app.modules.documents.schemas.search import SearchRequest
from app.modules.documents.services.context import has_usable_context
from app.modules.documents.services.search_service import SearchService


class AskService:
    """Answers questions using semantic search and a context-only answer provider."""

    def __init__(
        self,
        search_service: SearchService,
        answer_provider: AnswerProvider,
    ) -> None:
        self._search_service = search_service
        self._answer_provider = answer_provider

    def ask(self, document_id: str, request: AskRequest) -> AskResponse:
        """Retrieve relevant chunks and generate a grounded answer.

        Args:
            document_id: Identifier of the indexed document.
            request: Validated question-answering request.

        Returns:
            Generated answer and supporting source chunks.

        Raises:
            DocumentNotFoundError: If the document is not indexed.
            ValueError: If vector dimensions do not match stored embeddings.
        """
        search_response = self._search_service.search(
            document_id,
            SearchRequest(query=request.question, top_k=request.top_k),
        )
        if not has_usable_context(search_response.results):
            answer = INSUFFICIENT_CONTEXT_ANSWER
        else:
            answer = self._answer_provider.generate_answer(
                request.question,
                search_response.results,
            )
        sources = [
            AnswerSource(
                chunk_index=result.chunk_index,
                text=result.text,
                score=result.score,
            )
            for result in search_response.results
        ]

        return AskResponse(
            document_id=document_id,
            question=request.question,
            answer=answer,
            sources=sources,
            status="answered",
        )
