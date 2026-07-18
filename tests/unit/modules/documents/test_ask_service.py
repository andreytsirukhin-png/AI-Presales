import pytest

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.answers.constants import INSUFFICIENT_CONTEXT_ANSWER
from app.infrastructure.answers.mock_provider import MockAnswerProvider
from app.modules.documents.schemas.ask import AskRequest
from app.modules.documents.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.modules.documents.services.ask_service import AskService


class RecordingSearchService:
    """Test double that records search calls."""

    def __init__(self, response: SearchResponse | None = None) -> None:
        self.calls: list[tuple[str, SearchRequest]] = []
        self._response = response

    def search(self, document_id: str, request: SearchRequest) -> SearchResponse:
        self.calls.append((document_id, request))
        if self._response is None:
            raise DocumentNotFoundError(f"Document not found: {document_id}")
        return self._response


class RecordingAnswerProvider:
    """Test double that records answer generation calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, list[SearchResult]]] = []

    def generate_answer(
        self,
        question: str,
        context_chunks: list[SearchResult],
    ) -> str:
        self.calls.append((question, context_chunks))
        return "mock answer"


@pytest.fixture
def search_results() -> SearchResponse:
    return SearchResponse(
        document_id="doc-123",
        query="What integrations are required?",
        result_count=2,
        results=[
            SearchResult(
                chunk_index=0,
                text="ERP integrations are required.",
                score=0.91,
            ),
            SearchResult(
                chunk_index=1,
                text="Pricing details follow.",
                score=0.42,
            ),
        ],
    )


@pytest.fixture
def search_service(search_results: SearchResponse) -> RecordingSearchService:
    return RecordingSearchService(response=search_results)


@pytest.fixture
def answer_provider() -> RecordingAnswerProvider:
    return RecordingAnswerProvider()


@pytest.fixture
def ask_service(
    search_service: RecordingSearchService,
    answer_provider: RecordingAnswerProvider,
) -> AskService:
    return AskService(
        search_service=search_service,
        answer_provider=answer_provider,
    )


def test_ask_returns_expected_response(
    ask_service: AskService,
    search_service: RecordingSearchService,
    answer_provider: RecordingAnswerProvider,
    search_results: SearchResponse,
) -> None:
    request = AskRequest(question="What integrations are required?", top_k=3)

    result = ask_service.ask("doc-123", request)

    assert result.document_id == "doc-123"
    assert result.question == request.question
    assert result.answer == "mock answer"
    assert result.status == "answered"
    assert len(result.sources) == 2
    assert result.sources[0].chunk_index == 0
    assert result.sources[0].text == "ERP integrations are required."
    assert search_service.calls == [
        ("doc-123", SearchRequest(query=request.question, top_k=3)),
    ]
    assert answer_provider.calls == [(request.question, search_results.results)]


def test_ask_propagates_top_k(
    ask_service: AskService,
    search_service: RecordingSearchService,
) -> None:
    request = AskRequest(question="What integrations are required?", top_k=2)

    ask_service.ask("doc-123", request)

    assert search_service.calls[0][1].top_k == 2


def test_ask_raises_when_document_not_indexed() -> None:
    ask_service = AskService(
        search_service=RecordingSearchService(response=None),
        answer_provider=MockAnswerProvider(),
    )
    request = AskRequest(question="missing document", top_k=5)

    with pytest.raises(DocumentNotFoundError):
        ask_service.ask("missing-doc", request)


def test_ask_passes_retrieved_chunks_to_answer_provider(
    ask_service: AskService,
    answer_provider: RecordingAnswerProvider,
    search_results: SearchResponse,
) -> None:
    request = AskRequest(question="What integrations are required?", top_k=3)

    ask_service.ask("doc-123", request)

    assert answer_provider.calls == [(request.question, search_results.results)]


def test_ask_preserves_retrieved_chunk_order(
    answer_provider: RecordingAnswerProvider,
) -> None:
    search_response = SearchResponse(
        document_id="doc-123",
        query="ordered chunks",
        result_count=3,
        results=[
            SearchResult(chunk_index=2, text="third", score=0.3),
            SearchResult(chunk_index=0, text="first", score=0.9),
            SearchResult(chunk_index=1, text="second", score=0.6),
        ],
    )
    ask_service = AskService(
        search_service=RecordingSearchService(response=search_response),
        answer_provider=answer_provider,
    )
    request = AskRequest(question="ordered chunks", top_k=3)

    ask_service.ask("doc-123", request)

    assert [chunk.chunk_index for chunk in answer_provider.calls[0][1]] == [2, 0, 1]


def test_ask_does_not_invoke_provider_when_no_context_is_available() -> None:
    search_response = SearchResponse(
        document_id="doc-123",
        query="empty context",
        result_count=0,
        results=[],
    )
    answer_provider = RecordingAnswerProvider()
    ask_service = AskService(
        search_service=RecordingSearchService(response=search_response),
        answer_provider=answer_provider,
    )
    request = AskRequest(question="empty context", top_k=5)

    result = ask_service.ask("doc-123", request)

    assert answer_provider.calls == []
    assert result.answer == INSUFFICIENT_CONTEXT_ANSWER


def test_ask_returns_insufficient_context_response_when_all_chunks_are_empty() -> None:
    search_response = SearchResponse(
        document_id="doc-123",
        query="blank chunks",
        result_count=2,
        results=[
            SearchResult(chunk_index=0, text="   ", score=0.9),
            SearchResult(chunk_index=1, text="", score=0.8),
        ],
    )
    answer_provider = RecordingAnswerProvider()
    ask_service = AskService(
        search_service=RecordingSearchService(response=search_response),
        answer_provider=answer_provider,
    )
    request = AskRequest(question="blank chunks", top_k=5)

    result = ask_service.ask("doc-123", request)

    assert answer_provider.calls == []
    assert result.answer == INSUFFICIENT_CONTEXT_ANSWER
