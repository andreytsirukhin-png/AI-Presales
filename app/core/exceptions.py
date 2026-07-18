"""Application-level exceptions for upload validation."""


class UploadError(Exception):
    """Base class for upload validation failures."""


class UnsupportedFileTypeError(UploadError):
    """Raised when the uploaded file is not an allowed PDF."""


class FileTooLargeError(UploadError):
    """Raised when the uploaded file exceeds the size limit."""
