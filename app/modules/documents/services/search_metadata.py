"""Fill missing traceability metadata on search results."""

from datetime import UTC, datetime

from app.modules.documents.schemas.search import SearchResult
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.citations import metadata_from_stored
from app.modules.documents.services.metadata_service import MetadataService


def enrich_search_results(
    *,
    document_id: str,
    results: list[SearchResult],
    metadata_service: MetadataService,
    chunk_service: ChunkService,
    embedding_model: str,
) -> list[SearchResult]:
    """Ensure every search result includes source metadata for citations."""
    if not results:
        return results
    if all(result.metadata is not None for result in results):
        return results

    document_metadata = metadata_service.get(document_id)
    chunk_response = chunk_service.chunk(document_id)
    chunks_by_index = {chunk.index: chunk for chunk in chunk_response.chunks}
    created_at = datetime.now(UTC).isoformat()

    enriched: list[SearchResult] = []
    for result in results:
        if result.metadata is not None:
            enriched.append(result)
            continue

        chunk = chunks_by_index.get(result.chunk_index)
        metadata = metadata_from_stored(
            document_id=document_id,
            document_name=document_metadata.filename,
            chunk_index=result.chunk_index,
            embedding_model=embedding_model,
            created_at=created_at,
            page_number=chunk.page_number if chunk else None,
            section=chunk.section if chunk else None,
            heading=chunk.heading if chunk else None,
        )
        enriched.append(result.model_copy(update={"metadata": metadata}))

    return enriched


def enrich_project_search_results(
    *,
    project: object,
    results: list[SearchResult],
    embedding_model: str,
) -> list[SearchResult]:
    """Ensure project search results include project and document metadata."""
    if not results:
        return results

    project_id = getattr(project, "project_id")
    project_name = getattr(project, "project_name")
    enriched: list[SearchResult] = []
    for result in results:
        metadata = result.metadata
        if metadata is None:
            enriched.append(result)
            continue
        if metadata.project_id and metadata.project_name:
            enriched.append(result)
            continue
        enriched.append(
            result.model_copy(
                update={
                    "metadata": metadata.model_copy(
                        update={
                            "project_id": metadata.project_id or project_id,
                            "project_name": metadata.project_name or project_name,
                        }
                    )
                }
            )
        )
    return enriched
