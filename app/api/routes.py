from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.exceptions import (
    DocumentNotFoundError,
    EmptyPdfError,
    FileTooLargeError,
    InvalidPdfError,
    UnsupportedFileTypeError,
)
from app.infrastructure.storage import LocalFileStorage
from app.models.analysis import AnalysisResult
from app.models.document import UploadResponse
from app.modules.documents.schemas.parse import ParseResponse
from app.modules.documents.services.parse_service import ParseService
from app.services.demo_analysis import build_demo_analysis
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1")
_storage = LocalFileStorage()
upload_service = UploadService(_storage)
parse_service = ParseService(_storage)


@router.post("/documents/upload", response_model=UploadResponse, tags=["documents"])
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    try:
        return upload_service.upload(file.filename, content)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.post(
    "/documents/{document_id}/parse",
    response_model=ParseResponse,
    tags=["documents"],
)
async def parse_document(document_id: str) -> ParseResponse:
    """Extract text and page metadata from a previously uploaded PDF."""
    try:
        return parse_service.parse(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (InvalidPdfError, EmptyPdfError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analysis/demo", response_model=AnalysisResult, tags=["analysis"])
async def demo_analysis() -> AnalysisResult:
    return build_demo_analysis()
