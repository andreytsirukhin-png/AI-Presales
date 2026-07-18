import pytest

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.in_memory_store import InMemoryVectorStore
from app.infrastructure.vector_store.similarity import cosine_similarity
from app.modules.documents.schemas.embedding import Embedding


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


def test_upsert_and_get_returns_stored_embeddings(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-123"
    embeddings = [
        Embedding(index=0, text="first chunk", vector=[0.1, 0.2, 0.3]),
        Embedding(index=1, text="second chunk", vector=[0.4, 0.5, 0.6]),
    ]

    vector_store.upsert(document_id, embeddings)
    stored = vector_store.get(document_id)

    assert len(stored) == 2
    assert stored[0].index == 0
    assert stored[0].text == "first chunk"
    assert stored[0].vector == [0.1, 0.2, 0.3]
    assert stored[1].index == 1
    assert stored[1].text == "second chunk"
    assert stored[1].vector == [0.4, 0.5, 0.6]


def test_upsert_replaces_existing_embeddings(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-123"
    vector_store.upsert(
        document_id,
        [Embedding(index=0, text="old chunk", vector=[0.1, 0.2])],
    )
    vector_store.upsert(
        document_id,
        [
            Embedding(index=0, text="new first", vector=[0.9, 0.8]),
            Embedding(index=1, text="new second", vector=[0.7, 0.6]),
        ],
    )

    stored = vector_store.get(document_id)

    assert len(stored) == 2
    assert stored[0].vector == [0.9, 0.8]
    assert stored[1].vector == [0.7, 0.6]


def test_get_raises_when_document_not_indexed(
    vector_store: InMemoryVectorStore,
) -> None:
    with pytest.raises(DocumentNotFoundError):
        vector_store.get("missing-doc")


def test_search_returns_most_similar_chunks_first(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-search"
    vector_store.upsert(
        document_id,
        [
            Embedding(index=0, text="orthogonal", vector=[0.0, 1.0]),
            Embedding(index=1, text="closest", vector=[1.0, 0.0]),
            Embedding(index=2, text="middle", vector=[0.7, 0.7]),
        ],
    )

    results = vector_store.search(document_id, [1.0, 0.0], top_k=3)

    assert [result.chunk_index for result in results] == [1, 2, 0]
    assert results[0].score == pytest.approx(1.0)
    assert results[0].text == "closest"


def test_search_respects_top_k(vector_store: InMemoryVectorStore) -> None:
    document_id = "doc-top-k"
    vector_store.upsert(
        document_id,
        [
            Embedding(index=0, text="one", vector=[1.0, 0.0]),
            Embedding(index=1, text="two", vector=[0.8, 0.2]),
            Embedding(index=2, text="three", vector=[0.6, 0.4]),
        ],
    )

    results = vector_store.search(document_id, [1.0, 0.0], top_k=2)

    assert len(results) == 2


def test_search_only_within_requested_document(
    vector_store: InMemoryVectorStore,
) -> None:
    vector_store.upsert(
        "doc-a",
        [Embedding(index=0, text="doc a chunk", vector=[1.0, 0.0])],
    )
    vector_store.upsert(
        "doc-b",
        [Embedding(index=0, text="doc b chunk", vector=[0.0, 1.0])],
    )

    results = vector_store.search("doc-a", [1.0, 0.0], top_k=5)

    assert len(results) == 1
    assert results[0].text == "doc a chunk"


def test_search_uses_chunk_index_as_tie_breaker(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-tie"
    vector_store.upsert(
        document_id,
        [
            Embedding(index=2, text="later index", vector=[1.0, 0.0]),
            Embedding(index=0, text="earlier index", vector=[1.0, 0.0]),
            Embedding(index=1, text="middle index", vector=[1.0, 0.0]),
        ],
    )

    results = vector_store.search(document_id, [1.0, 0.0], top_k=3)

    assert [result.chunk_index for result in results] == [0, 1, 2]
    assert all(result.score == pytest.approx(1.0) for result in results)


def test_search_handles_zero_vectors_safely(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-zero"
    vector_store.upsert(
        document_id,
        [Embedding(index=0, text="zero chunk", vector=[0.0, 0.0])],
    )

    results = vector_store.search(document_id, [0.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].score == 0.0


def test_search_raises_for_dimension_mismatch(
    vector_store: InMemoryVectorStore,
) -> None:
    vector_store.upsert(
        "doc-dim",
        [Embedding(index=0, text="two dims", vector=[1.0, 0.0])],
    )

    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        vector_store.search("doc-dim", [1.0, 0.0, 0.0], top_k=1)


def test_search_raises_when_document_not_indexed(
    vector_store: InMemoryVectorStore,
) -> None:
    with pytest.raises(DocumentNotFoundError):
        vector_store.search("missing-doc", [1.0, 0.0], top_k=1)


def test_cosine_similarity_returns_zero_for_zero_vector() -> None:
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0
