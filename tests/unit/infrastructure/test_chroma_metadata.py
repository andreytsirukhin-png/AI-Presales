from app.infrastructure.vector_store.chroma_metadata import metadata_from_chroma, metadata_to_chroma
from app.modules.documents.schemas.source_metadata import SourceMetadata


def test_metadata_round_trip_for_chroma() -> None:
    original = SourceMetadata(
        document_id="doc-abc",
        document_name="proposal.pdf",
        page_number=7,
        chunk_id="doc-abc-chunk-2",
        chunk_index=2,
        embedding_model="text-embedding-3-small",
        created_at="2026-07-20T12:00:00+00:00",
        heading="Scope",
    )

    chroma_payload = metadata_to_chroma(original)
    restored = metadata_from_chroma(chroma_payload)

    assert restored == original
