"""Application-level exceptions for document upload and parsing."""


class UploadError(Exception):
    """Base class for upload validation failures."""


class UnsupportedFileTypeError(UploadError):
    """Raised when the uploaded file is not an allowed PDF."""


class FileTooLargeError(UploadError):
    """Raised when the uploaded file exceeds the size limit."""


class ParseError(Exception):
    """Base class for document parse failures."""


class DocumentNotFoundError(ParseError):
    """Raised when a document identifier does not map to stored content."""


class InvalidPdfError(ParseError):
    """Raised when PDF bytes cannot be read as a valid document."""


class EmptyPdfError(ParseError):
    """Raised when a PDF has no extractable text content."""
