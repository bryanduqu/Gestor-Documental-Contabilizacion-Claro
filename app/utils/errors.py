class DocumentProcessingError(Exception):
    """Base application exception."""


class EmptyPdfError(DocumentProcessingError):
    """Raised when the PDF is empty."""


class CorruptedPdfError(DocumentProcessingError):
    """Raised when the PDF cannot be read."""


class ClassificationError(DocumentProcessingError):
    """Raised when the classifier fails."""


class ExtractionError(DocumentProcessingError):
    """Raised when the extraction stage fails."""


class ModelTimeoutError(DocumentProcessingError):
    """Raised when the model request times out."""


class ApiProviderError(DocumentProcessingError):
    """Raised when the upstream API fails."""


class DocumentNotFoundError(DocumentProcessingError):
    """Raised when a processed document cannot be found."""
