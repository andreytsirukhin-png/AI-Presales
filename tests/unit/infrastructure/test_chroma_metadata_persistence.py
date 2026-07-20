from app.infrastructure.vector_store.chroma_store import ChromaVectorStore
from app.modules.documents.schemas.embedding import Embedding
from app.modules.documents.schemas.source_metadata import SourceMetadata


def test_chroma_persists_full_source_metadata(tmp_path) -> None:
    store = ChromaVectorStore(persist_path=str(tmp_path / "chroma"))
    store.clear()
    metadata = SourceMetadata(
        document_id="doc-1",
        document_name="RFP.pdf",
        page_number=3,
        chunk_id="doc-1-chunk-0",
        chunk_index=0,
        embedding_model="mock",
        created_at="2026-07-20T12:00:00+00:00",
    )
    store.add_documents(
        "doc-1",
        [Embedding(index=0, text="indexed chunk", vector=[1.0, 0.0], metadata=metadata)],
    )

    reloaded = ChromaVectorStore(persist_path=str(tmp_path / "chroma"))
    stored = reloaded.get("doc-1")

    assert stored[0].metadata == metadata
    search_hits = reloaded.search("doc-1", [1.0, 0.0], top_k=1)
    assert search_hits[0].metadata == metadata
