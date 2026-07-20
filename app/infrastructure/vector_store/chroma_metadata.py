"""Serialize source metadata for ChromaDB storage."""

from app.modules.documents.schemas.source_metadata import SourceMetadata


def metadata_to_chroma(metadata: SourceMetadata) -> dict[str, str | int]:
    """Convert source metadata to Chroma-compatible primitive values."""
    payload: dict[str, str | int] = {
        "document_id": metadata.document_id,
        "document_name": metadata.document_name,
        "chunk_id": metadata.chunk_id,
        "chunk_index": metadata.chunk_index,
        "embedding_model": metadata.embedding_model,
        "created_at": metadata.created_at,
    }
    if metadata.page_number is not None:
        payload["page_number"] = metadata.page_number
    if metadata.section:
        payload["section"] = metadata.section
    if metadata.heading:
        payload["heading"] = metadata.heading
    if metadata.project_id:
        payload["project_id"] = metadata.project_id
    if metadata.project_name:
        payload["project_name"] = metadata.project_name
    return payload


def metadata_from_chroma(data: dict[str, object]) -> SourceMetadata:
    """Rebuild source metadata from a Chroma metadata dictionary."""
    page_raw = data.get("page_number")
    page_number = int(page_raw) if page_raw is not None else None
    section_raw = data.get("section")
    heading_raw = data.get("heading")
    project_id_raw = data.get("project_id")
    project_name_raw = data.get("project_name")
    return SourceMetadata(
        document_id=str(data["document_id"]),
        document_name=str(data["document_name"]),
        page_number=page_number,
        chunk_id=str(data["chunk_id"]),
        chunk_index=int(data["chunk_index"]),
        embedding_model=str(data["embedding_model"]),
        created_at=str(data["created_at"]),
        section=str(section_raw) if section_raw else None,
        heading=str(heading_raw) if heading_raw else None,
        project_id=str(project_id_raw) if project_id_raw else None,
        project_name=str(project_name_raw) if project_name_raw else None,
    )
