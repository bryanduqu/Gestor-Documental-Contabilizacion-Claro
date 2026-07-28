from __future__ import annotations

from functools import lru_cache

from app.classifiers.azure_classifier import AzureDocumentIntelligenceClassifier
from app.config.settings import Settings, get_settings
from app.repositories.document_repository import InMemoryDocumentRepository
from app.services.azure_document_intelligence import AzureDocumentIntelligenceService
from app.services.document_processor import DocumentProcessingService


class Container:
    """Build and expose application dependencies."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.repository = InMemoryDocumentRepository()
        self.azure_client = AzureDocumentIntelligenceService(
            endpoint=self.settings.azure_document_intelligence_endpoint,
            key=self.settings.azure_document_intelligence_key,
        )
        self.classifier = AzureDocumentIntelligenceClassifier(
            azure_client=self.azure_client,
            classifier_id=self.settings.azure_document_intelligence_classifier_id,
        )
        self.document_service = DocumentProcessingService(
            classifier=self.classifier,
            repository=self.repository,
            settings=self.settings,
        )


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Return a new dependency container."""
    return Container()
