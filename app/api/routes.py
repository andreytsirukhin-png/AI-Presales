from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.infrastructure.storage import LocalFileStorage
from app.models.analysis import AnalysisResult
from app.models.document import UploadResponse
from app.modules.documents.api.routes import router as documents_router
from app.services.demo_analysis import build_demo_analysis
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1")
_storage = LocalFileStorage()
router.include_router(documents_router)
upload_service = UploadService(_storage)


@router.post("/documents/upload", response_model=UploadResponse, tags=["documents"])
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    content = await file.read()
    try:
        return upload_service.upload(
            file.filename,
            content,
            content_type=file.content_type,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc


@router.post("/analysis/demo", response_model=AnalysisResult, tags=["analysis"])
async def demo_analysis() -> AnalysisResult:
    return build_demo_analysis()
