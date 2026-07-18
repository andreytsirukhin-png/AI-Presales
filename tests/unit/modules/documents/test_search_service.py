import pytest

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.embeddings.mock_provider import MOCK_EMBEDDING_DIMENSION, MockEmbeddingProvider
from app.infrastructure.vector_store.in_memory_store import InMemoryVectorStore
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.search import SearchRequest
from app.modules.documents.services.search_service import SearchService


class RecordingEmbeddingProvider:
    """Test double that records embedding calls."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    @property
    def dimension(self) -> int:
        return MOCK_EMBEDDING_DIMENSION

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return MockEmbeddingProvider().embed(text)


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


@pytest.fixture
def provider() -> RecordingEmbeddingProvider:
    return RecordingEmbeddingProvider()


@pytest.fixture
def search_service(
    vector_store: InMemoryVectorStore,
    provider: RecordingEmbeddingProvider,
) -> SearchService:
    return SearchService(provider=provider, vector_store=vector_store)


def test_search_returns_expected_response(
    search_service: SearchService,
    vector_store: InMemoryVectorStore,
    provider: RecordingEmbeddingProvider,
) -> None:
    document_id = "doc-123"
    vector_store.upsert(
        document_id,
        [
            Embedding(
                index=0,
                text="integration requirements for ERP",
                vector=MockEmbeddingProvider().embed("integration requirements for ERP"),
            ),
            Embedding(
                index=1,
                text="pricing and licensing details",
                vector=MockEmbeddingProvider().embed("pricing and licensing details"),
            ),
        ],
    )
    request = SearchRequest(query="What integrations are required?", top_k=5)

    result = search_service.search(document_id, request)

    assert result.document_id == document_id
    assert result.query == request.query
    assert result.result_count == len(result.results)
    assert result.result_count >= 1
    assert provider.calls == [request.query]


def test_search_raises_when_document_not_indexed(
    search_service: SearchService,
) -> None:
    request = SearchRequest(query="missing document", top_k=3)

    with pytest.raises(DocumentNotFoundError):
        search_service.search("missing-doc", request)


def test_search_respects_top_k(
    search_service: SearchService,
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-top-k"
    vector_store.upsert(
        document_id,
        [
            Embedding(
                index=index,
                text=f"chunk {index}",
                vector=MockEmbeddingProvider().embed(f"chunk {index}"),
            )
            for index in range(5)
        ],
    )
    request = SearchRequest(query="chunk", top_k=2)

    result = search_service.search(document_id, request)

    assert result.result_count == 2
    assert len(result.results) == 2
