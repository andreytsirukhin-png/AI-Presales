from fastapi import APIRouter, HTTPException

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.infrastructure.embeddings import MockEmbeddingProvider
from app.infrastructure.storage import LocalFileStorage
from app.infrastructure.vector_store import InMemoryVectorStore
from app.modules.documents.schemas.chunk import ChunkResponse
from app.modules.documents.schemas.document import DocumentMetadata
from app.modules.documents.schemas.embedding import EmbeddingResponse
from app.modules.documents.schemas.index import IndexResponse
from app.modules.documents.schemas.parse import ParseResponse
from app.modules.documents.services.chunk_service import ChunkService
from app.modules.documents.services.embedding_service import EmbeddingService
from app.modules.documents.services.index_service import IndexService
from app.modules.documents.services.metadata_service import MetadataService
from app.modules.documents.services.parse_service import ParseService

router = APIRouter(prefix="/documents", tags=["documents"])
_storage = LocalFileStorage()
_vector_store = InMemoryVectorStore()
parse_service = ParseService(_storage)
metadata_service = MetadataService(_storage)
chunk_service = ChunkService(_storage)
embedding_service = EmbeddingService(
    metadata_service=metadata_service,
    chunk_service=chunk_service,
    provider=MockEmbeddingProvider(),
)
index_service = IndexService(
    embedding_service=embedding_service,
    vector_store=_vector_store,
)


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document_metadata(document_id: str) -> DocumentMetadata:
    """Return stored metadata for a previously uploaded document."""
    try:
        return metadata_service.get(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{document_id}/parse", response_model=ParseResponse)
async def parse_document(document_id: str) -> ParseResponse:
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
async def chunk_document(document_id: str) -> ChunkResponse:
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
async def embed_document(document_id: str) -> EmbeddingResponse:
    """Generate embeddings for a previously uploaded PDF document."""
    try:
        return embedding_service.embed(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{document_id}/index", response_model=IndexResponse)
async def index_document(document_id: str) -> IndexResponse:
    """Index embeddings for a previously uploaded PDF document."""
    try:
        return index_service.index(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except EmptyPdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
