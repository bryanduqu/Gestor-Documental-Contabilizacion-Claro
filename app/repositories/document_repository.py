from __future__ import annotations

from app.schemas.common import ProcessedDocumentResponse
from app.utils.errors import DocumentNotFoundError


class InMemoryDocumentRepository:
    """Simple repository for processed documents."""

    def __init__(self) -> None:
        self._documents: dict[str, ProcessedDocumentResponse] = {}

    def save(self, document: ProcessedDocumentResponse) -> ProcessedDocumentResponse:
        self._documents[document.id] = document
        return document

    def get(self, document_id: str) -> ProcessedDocumentResponse:
        document = self._documents.get(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document with id '{document_id}' was not found.")
        return document
