from pathlib import Path

import pytest

from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.services.upload_service import UploadService

PDF_CONTENT = b"%PDF-1.4 minimal test content"


class FakeFileStorage:
    """In-memory storage adapter for unit tests."""

    def __init__(self) -> None:
        self.saved_files: dict[str, bytes] = {}

    def save(self, relative_path: str, content: bytes) -> None:
        self.saved_files[relative_path] = content

    def read(self, relative_path: str) -> bytes:
        try:
            return self.saved_files[relative_path]
        except KeyError as exc:
            raise FileNotFoundError(relative_path) from exc


@pytest.fixture
def storage() -> FakeFileStorage:
    return FakeFileStorage()


@pytest.fixture
def upload_service(storage: FakeFileStorage) -> UploadService:
    return UploadService(storage, max_upload_bytes=1024)


def test_upload_pdf_returns_expected_response(upload_service: UploadService, storage: FakeFileStorage) -> None:
    result = upload_service.upload("proposal.pdf", PDF_CONTENT)

    assert result.status == "uploaded"
    assert result.filename == "proposal.pdf"
    assert result.document_id
    assert len(storage.saved_files) == 1
    saved_path = next(iter(storage.saved_files))
    assert saved_path.endswith(".pdf")
    assert storage.saved_files[saved_path] == PDF_CONTENT


def test_upload_rejects_non_pdf_extension(upload_service: UploadService) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        upload_service.upload("notes.txt", PDF_CONTENT)


def test_upload_rejects_invalid_pdf_content(upload_service: UploadService) -> None:
    with pytest.raises(UnsupportedFileTypeError):
        upload_service.upload("proposal.pdf", b"not a pdf")


def test_upload_rejects_file_over_size_limit(storage: FakeFileStorage) -> None:
    service = UploadService(storage, max_upload_bytes=10)

    with pytest.raises(FileTooLargeError):
        service.upload("proposal.pdf", PDF_CONTENT)


def test_upload_uses_pdf_extension_when_filename_missing(upload_service: UploadService, storage: FakeFileStorage) -> None:
    result = upload_service.upload(None, PDF_CONTENT)

    assert result.filename == "document.pdf"
    saved_path = next(iter(storage.saved_files))
    assert Path(saved_path).suffix == ".pdf"
