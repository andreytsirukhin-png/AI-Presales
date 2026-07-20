import pytest

from app.core.exceptions import DocumentNotFoundError
from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from app.modules.documents.schemas.embedding import Embedding


@pytest.fixture
def vector_store(tmp_path: pytest.TempPathFactory) -> ChromaVectorStore:
    store = ChromaVectorStore(persist_path=str(tmp_path / "chroma"))
    store.clear()
    return store


def test_create_collection_starts_empty(vector_store: ChromaVectorStore) -> None:
    assert vector_store.count() == 0


def test_add_documents_indexes_chunks(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-1",
        [
            Embedding(index=0, text="first", vector=[1.0, 0.0]),
            Embedding(index=1, text="second", vector=[0.0, 1.0]),
        ],
    )

    assert vector_store.count() == 2
    stored = vector_store.get("doc-1")
    assert [chunk.index for chunk in stored] == [0, 1]


def test_add_documents_replaces_existing_document(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-1",
        [Embedding(index=0, text="old", vector=[1.0, 0.0])],
    )
    vector_store.add_documents(
        "doc-1",
        [Embedding(index=0, text="new", vector=[0.0, 1.0])],
    )

    stored = vector_store.get("doc-1")
    assert len(stored) == 1
    assert stored[0].text == "new"


def test_search_returns_document_scoped_results(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-a",
        [Embedding(index=0, text="doc a", vector=[1.0, 0.0])],
    )
    vector_store.add_documents(
        "doc-b",
        [Embedding(index=0, text="doc b", vector=[0.0, 1.0])],
    )

    results = vector_store.search("doc-a", [1.0, 0.0], top_k=5)

    assert len(results) == 1
    assert results[0].text == "doc a"


def test_delete_document_removes_chunks(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-1",
        [Embedding(index=0, text="delete me", vector=[1.0, 0.0])],
    )

    vector_store.delete_document("doc-1")

    assert vector_store.count() == 0
    with pytest.raises(DocumentNotFoundError):
        vector_store.get("doc-1")


def test_clear_removes_all_documents(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-1",
        [Embedding(index=0, text="one", vector=[1.0, 0.0])],
    )
    vector_store.add_documents(
        "doc-2",
        [Embedding(index=0, text="two", vector=[0.0, 1.0])],
    )

    vector_store.clear()

    assert vector_store.count() == 0


def test_search_raises_for_dimension_mismatch(vector_store: ChromaVectorStore) -> None:
    vector_store.add_documents(
        "doc-dim",
        [Embedding(index=0, text="two dims", vector=[1.0, 0.0])],
    )

    with pytest.raises(ValueError, match="Vector dimension mismatch"):
        vector_store.search("doc-dim", [1.0, 0.0, 0.0], top_k=1)


def test_search_raises_when_document_not_indexed(vector_store: ChromaVectorStore) -> None:
    with pytest.raises(DocumentNotFoundError):
        vector_store.search("missing-doc", [1.0, 0.0], top_k=1)
