from fastapi import APIRouter, HTTPException

from app.core.exceptions import DocumentNotFoundError, EmptyPdfError, InvalidPdfError
from app.infrastructure.storage import LocalFileStorage
from app.modules.documents.schemas.parse import ParseResponse
from app.modules.documents.services.parse_service import ParseService

router = APIRouter(prefix="/documents", tags=["documents"])
parse_service = ParseService(LocalFileStorage())


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
