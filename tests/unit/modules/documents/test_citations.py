from app.modules.documents.schemas.ask import AnswerCitation
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.schemas.source_metadata import SourceMetadata
from app.modules.documents.services.citations import (
    build_answer_sources,
    build_citations,
    metadata_from_stored,
)


def _metadata(**overrides: object) -> SourceMetadata:
    base = metadata_from_stored(
        document_id="doc-1",
        document_name="RFP.pdf",
        chunk_index=3,
        embedding_model="mock",
        created_at="2026-01-01T00:00:00+00:00",
        page_number=12,
    )
    return base.model_copy(update=overrides)


def test_build_citations_deduplicates_by_document_page_and_chunk() -> None:
    metadata = _metadata()
    results = [
        SearchResult(chunk_index=3, text="a", score=0.9, metadata=metadata),
        SearchResult(chunk_index=3, text="b", score=0.8, metadata=metadata),
    ]

    citations = build_citations(results)

    assert citations == [
        AnswerCitation(
            document="RFP.pdf",
            page=12,
            score=0.9,
            chunk_index=3,
            chunk_id="doc-1-chunk-3",
        )
    ]


def test_build_answer_sources_includes_metadata() -> None:
    metadata = _metadata()
    results = [
        SearchResult(chunk_index=1, text="chunk text", score=0.75, metadata=metadata),
    ]

    sources = build_answer_sources(results)

    assert len(sources) == 1
    assert sources[0].metadata == metadata
    assert sources[0].text == "chunk text"
