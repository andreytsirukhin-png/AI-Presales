from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.dependencies import (
    get_project_ask_service,
    get_project_document_service,
    get_project_search_service,
    get_project_service,
)
from app.core.exceptions import (
    AnswerError,
    DocumentNotFoundError,
    EmbeddingError,
    EmptyPdfError,
    FileTooLargeError,
    InvalidPdfError,
    ProjectNotFoundError,
    UnsupportedFileTypeError,
)
from app.core.config import Settings, get_settings
from app.modules.documents.schemas.search import SearchRequest
from app.modules.projects.schemas.document import (
    ProjectDocumentListResponse,
    ProjectDocumentUploadResponse,
)
from app.modules.projects.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectStatisticsResponse,
)
from app.modules.projects.schemas.search import ProjectAskRequest, ProjectAskResponse, ProjectSearchResponse
from app.modules.projects.services.document_service import ProjectDocumentService
from app.modules.projects.services.project_service import ProjectService
from app.modules.projects.services.search_service import ProjectAskService, ProjectSearchService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create a new multi-document workspace project."""
    return project_service.create(request)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectListResponse:
    """List all workspace projects."""
    projects = project_service.list_projects()
    return ProjectListResponse(projects=projects, count=len(projects))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Return metadata for one project."""
    try:
        return project_service.get(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    document_service: ProjectDocumentService = Depends(get_project_document_service),
) -> None:
    """Delete a project and all associated documents."""
    try:
        project = project_service.require_metadata(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    for document_id in list(project.document_ids):
        try:
            document_service.delete_document(project_id, document_id)
        except DocumentNotFoundError:
            continue
    project_service.delete(project_id)


@router.get("/{project_id}/statistics", response_model=ProjectStatisticsResponse)
async def project_statistics(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    settings: Settings = Depends(get_settings),
) -> ProjectStatisticsResponse:
    """Return indexing and runtime statistics for a project."""
    from app.core.dependencies import build_vector_store
    from app.modules.documents.services.embedding_service import resolve_embedding_model

    try:
        project = project_service.require_metadata(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    vector_store = build_vector_store(settings.vector_store, settings.vector_db_path)
    indexed_chunks = vector_store.count_documents(project.document_ids)
    return project_service.statistics(
        project_id,
        indexed_chunks=indexed_chunks,
        embedding_provider=settings.embedding_provider,
        embedding_model=resolve_embedding_model(settings),
        vector_store=settings.vector_store,
    )


@router.post("/{project_id}/documents", response_model=ProjectDocumentUploadResponse)
async def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
    document_service: ProjectDocumentService = Depends(get_project_document_service),
) -> ProjectDocumentUploadResponse:
    """Upload a PDF into a project and index it automatically."""
    content = await file.read()
    try:
        return document_service.upload_and_index(
            project_id,
            file.filename,
            content,
            content_type=file.content_type,
        )
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except (InvalidPdfError, EmptyPdfError, EmbeddingError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{project_id}/documents", response_model=ProjectDocumentListResponse)
async def list_project_documents(
    project_id: str,
    document_service: ProjectDocumentService = Depends(get_project_document_service),
) -> ProjectDocumentListResponse:
    """List documents belonging to a project."""
    try:
        return document_service.list_documents(project_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{project_id}/documents/{document_id}", status_code=204)
async def delete_project_document(
    project_id: str,
    document_id: str,
    document_service: ProjectDocumentService = Depends(get_project_document_service),
) -> None:
    """Remove one document from a project."""
    try:
        document_service.delete_document(project_id, document_id)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{project_id}/search", response_model=ProjectSearchResponse)
async def search_project(
    project_id: str,
    request: SearchRequest,
    search_service: ProjectSearchService = Depends(get_project_search_service),
) -> ProjectSearchResponse:
    """Run semantic search across all indexed documents in a project."""
    try:
        return search_service.search(project_id, request)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{project_id}/ask", response_model=ProjectAskResponse)
async def ask_project(
    project_id: str,
    request: ProjectAskRequest,
    ask_service: ProjectAskService = Depends(get_project_ask_service),
) -> ProjectAskResponse:
    """Answer a question using project-wide retrieved context."""
    try:
        return ask_service.ask(project_id, request)
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnswerError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
