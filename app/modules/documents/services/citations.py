from app.modules.documents.schemas.ask import AnswerCitation, AnswerSource
from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.schemas.source_metadata import SourceMetadata


def build_citations(results: list[SearchResult]) -> list[AnswerCitation]:
    """Build compact citation entries from ranked search results."""
    citations: list[AnswerCitation] = []
    seen: set[tuple[str, int | None, int]] = set()

    for result in results:
        metadata = result.metadata
        document_name = metadata.document_name if metadata else "document"
        page_number = metadata.page_number if metadata else None
        chunk_index = result.chunk_index
        chunk_id = metadata.chunk_id if metadata else None
        dedupe_key = (document_name, page_number, chunk_index)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        citations.append(
            AnswerCitation(
                document=document_name,
                page=page_number,
                score=result.score,
                chunk_index=chunk_index,
                chunk_id=chunk_id,
            )
        )

    return citations


def build_answer_sources(results: list[SearchResult]) -> list[AnswerSource]:
    """Build API source payloads including metadata for each retrieved chunk."""
    return [
        AnswerSource(
            chunk_index=result.chunk_index,
            text=result.text,
            score=result.score,
            metadata=result.metadata,
        )
        for result in results
    ]


def metadata_from_stored(
    *,
    document_id: str,
    document_name: str,
    chunk_index: int,
    embedding_model: str,
    created_at: str,
    page_number: int | None = None,
    section: str | None = None,
    heading: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
) -> SourceMetadata:
    """Create source metadata for a chunk being indexed."""
    from app.modules.documents.schemas.source_metadata import build_chunk_id

    return SourceMetadata(
        document_id=document_id,
        document_name=document_name,
        page_number=page_number,
        chunk_id=build_chunk_id(document_id, chunk_index),
        chunk_index=chunk_index,
        embedding_model=embedding_model,
        created_at=created_at,
        section=section,
        heading=heading,
        project_id=project_id,
        project_name=project_name,
    )
