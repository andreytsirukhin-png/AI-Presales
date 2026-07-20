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


class ProjectNotFoundError(ParseError):
    """Raised when a requested project workspace does not exist."""


class ProposalNotFoundError(ParseError):
    """Raised when a requested project proposal does not exist."""


class InvalidPdfError(ParseError):
    """Raised when PDF bytes cannot be parsed."""


class EmptyPdfError(ParseError):
    """Raised when a PDF contains no extractable text."""


class EmbeddingError(Exception):
    """Base class for embedding provider failures."""


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when embedding provider configuration is invalid."""


class EmbeddingProviderError(EmbeddingError):
    """Raised when an embedding provider request fails."""


class InvalidEmbeddingDimensionError(EmbeddingError):
    """Raised when an embedding provider returns an unexpected vector size."""


class AnswerError(Exception):
    """Base class for answer provider failures."""


class AnswerConfigurationError(AnswerError):
    """Raised when answer provider configuration is invalid."""


class AnswerProviderError(AnswerError):
    """Raised when an answer provider request fails."""
