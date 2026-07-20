import pytest

from app.core.dependencies import build_vector_store, clear_dependency_caches
from app.infrastructure.vector_store import ChromaVectorStore, InMemoryVectorStore
from app.modules.documents.schemas.embedding import Embedding


def test_build_vector_store_returns_inmemory_by_default() -> None:
    store = build_vector_store("inmemory", "./vector_store")

    assert isinstance(store, InMemoryVectorStore)


def test_build_vector_store_returns_chroma_store(tmp_path: pytest.TempPathFactory) -> None:
    clear_dependency_caches()
    persist_path = tmp_path / "chroma-db"
    store = build_vector_store("chroma", str(persist_path))

    assert isinstance(store, ChromaVectorStore)


def test_build_vector_store_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported vector store"):
        build_vector_store("postgres", "./vector_store")


def test_different_chroma_paths_create_different_cached_instances(
    tmp_path: pytest.TempPathFactory,
) -> None:
    clear_dependency_caches()
    first = build_vector_store("chroma", str(tmp_path / "one"))
    second = build_vector_store("chroma", str(tmp_path / "two"))

    assert first is not second


def test_chroma_vector_store_persists_across_instances(
    tmp_path: pytest.TempPathFactory,
) -> None:
    persist_path = str(tmp_path / "persist")
    document_id = "doc-persist"
    embeddings = [
        Embedding(index=0, text="persistent chunk", vector=[1.0, 0.0, 0.0]),
    ]

    first = ChromaVectorStore(persist_path=persist_path)
    first.add_documents(document_id, embeddings)
    assert first.count() == 1

    reloaded = ChromaVectorStore(persist_path=persist_path)
    stored = reloaded.get(document_id)

    assert len(stored) == 1
    assert stored[0].text == "persistent chunk"

    results = reloaded.search(document_id, [1.0, 0.0, 0.0], top_k=1)
    assert results[0].text == "persistent chunk"
    assert results[0].score == pytest.approx(1.0, abs=1e-6)
