from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import (
    get_ask_service,
    get_chunk_service,
    get_embedding_service,
    get_index_service,
    get_metadata_service,
    get_parse_service,
    get_search_service,
)
from app.core.exceptions import (
    DocumentNotFoundError,
    EmbeddingError,
    EmptyPdfError,
    InvalidPdfError,
)
from app.modules.documents.schemas.ask import AskRequest, AskResponse
from app.modules.documents.schemas.chunk import ChunkResponse
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.schemas.embedding import EmbeddingResponse
from app.modules.documents.schemas.index import IndexResponse
from app.modules.documents.schemas.parse import ParseResponse
from app.modules.documents.schemas.search import SearchRequest, SearchResponse
from app.modules.documents.services.ask_service import AskService
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.documents.services.parse_service import ParseService
from app.modules.documents.services.search_service import SearchService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document_metadata(
    document_id: str,
    metadata_service: MetadataService = Depends(get_metadata_service),
) -> DocumentMetadata:
    """Return stored metadata for a previously uploaded document."""
    try:
        return metadata_service.get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{document_id}/parse", response_model=ParseResponse)
async def parse_document(
    document_id: str,
    parse_service: ParseService = Depends(get_parse_service),
) -> ParseResponse:
    """Extract text from a previously uploaded PDF document."""
    try:
        return parse_service.parse(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/chunks", response_model=ChunkResponse)
async def chunk_document(
    document_id: str,
    chunk_service: ChunkService = Depends(get_chunk_service),
) -> ChunkResponse:
    """Split a previously uploaded PDF into ordered text chunks."""
    try:
        return chunk_service.chunk(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/embeddings", response_model=EmbeddingResponse)
async def embed_document(
    document_id: str,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> EmbeddingResponse:
    """Generate embeddings for a previously uploaded PDF document."""
    try:
        return embedding_service.embed(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/index", response_model=IndexResponse)
async def index_document(
    document_id: str,
    index_service: IndexService = Depends(get_index_service),
) -> IndexResponse:
    """Index embeddings for a previously uploaded PDF document."""
    try:
        return index_service.index(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/search", response_model=SearchResponse)
async def search_document(
    document_id: str,
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    """Search indexed chunks within a previously uploaded PDF document."""
    try:
        return search_service.search(document_id, request)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/ask", response_model=AskResponse)
async def ask_document(
    document_id: str,
    request: AskRequest,
    ask_service: AskService = Depends(get_ask_service),
) -> AskResponse:
    """Answer a question using indexed document context."""
    try:
        return ask_service.ask(document_id, request)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
