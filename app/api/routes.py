from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.analysis import AnalysisResult
from app.services.demo_analysis import build_demo_analysis

router = APIRouter(prefix="/api/v1")
UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@router.post("/documents/upload", tags=["documents"])
async def upload_document(file: UploadFile = File(...)) -> dict[str, str | int]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit.")

    UPLOAD_DIR.mkdir(exist_ok=True)
    document_id = str(uuid4())
    destination = UPLOAD_DIR / f"{document_id}{suffix}"
    destination.write_bytes(content)

    return {
        "document_id": document_id,
        "filename": file.filename or destination.name,
        "size_bytes": len(content),
        "status": "uploaded",
    }


@router.post("/analysis/demo", response_model=AnalysisResult, tags=["analysis"])
async def demo_analysis() -> AnalysisResult:
    return build_demo_analysis()
