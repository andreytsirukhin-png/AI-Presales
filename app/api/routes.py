from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import Settings, get_settings
from app.core.dependencies import get_upload_service
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.models.analysis import AnalysisResult
from app.models.document import UploadResponse
from app.modules.documents.api.routes import router as documents_router
from app.modules.projects.api.routes import router as projects_router
from app.schemas.status import PlatformStatusResponse, build_platform_status
from app.services.demo_analysis import build_demo_analysis
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/v1")
router.include_router(documents_router)
router.include_router(projects_router)


@router.post("/documents/upload", response_model=UploadResponse, tags=["documents"])
async def upload_document(
    file: UploadFile = File(...),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
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


@router.get("/status", response_model=PlatformStatusResponse, tags=["system"])
async def platform_status(
    settings: Settings = Depends(get_settings),
) -> PlatformStatusResponse:
    """Return runtime provider configuration for clients and the demo UI."""
    return build_platform_status(settings)
