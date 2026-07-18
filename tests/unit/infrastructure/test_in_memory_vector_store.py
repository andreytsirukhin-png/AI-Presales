import pytest

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.in_memory_store import InMemoryVectorStore
from app.modules.documents.schemas.embedding import Embedding


@pytest.fixture
def vector_store() -> InMemoryVectorStore:
    return InMemoryVectorStore()


def test_upsert_and_get_returns_stored_embeddings(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-123"
    embeddings = [
        Embedding(index=0, vector=[0.1, 0.2, 0.3]),
        Embedding(index=1, vector=[0.4, 0.5, 0.6]),
    ]

    vector_store.upsert(document_id, embeddings)
    stored = vector_store.get(document_id)

    assert len(stored) == 2
    assert stored[0].index == 0
    assert stored[0].vector == [0.1, 0.2, 0.3]
    assert stored[1].index == 1
    assert stored[1].vector == [0.4, 0.5, 0.6]


def test_upsert_replaces_existing_embeddings(
    vector_store: InMemoryVectorStore,
) -> None:
    document_id = "doc-123"
    vector_store.upsert(
        document_id,
        [Embedding(index=0, vector=[0.1, 0.2])],
    )
    vector_store.upsert(
        document_id,
        [Embedding(index=0, vector=[0.9, 0.8]), Embedding(index=1, vector=[0.7, 0.6])],
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
