"""Application-level exceptions for document upload and parsing."""


class UploadError(Exception):
    """Base class for upload validation failures."""


class UnsupportedFileTypeError(UploadError):
    """Raised when the uploaded file is not an allowed PDF."""


class FileTooLargeError(UploadError):
    """Raised when the uploaded file exceeds the size limit."""


class ParseError(Exception):
    """Base class for document parsing failures."""


class DocumentNotFoundError(ParseError):
    """Raised when a requested document does not exist in storage."""


class InvalidPdfError(ParseError):
    """Raised when PDF bytes cannot be parsed."""


class EmptyPdfError(ParseError):
    """Raised when a PDF contains no extractable text."""
