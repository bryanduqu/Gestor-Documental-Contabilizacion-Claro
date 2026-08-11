from __future__ import annotations

from functools import lru_cache

from app.classifiers.azure_classifier import AzureDocumentIntelligenceClassifier
from app.classifiers.routing_classifier import RoutingDocumentClassifier
from app.config.settings import Settings, get_extraction_model_mapping, get_settings
from app.repositories.document_repository import InMemoryDocumentRepository
from app.services.azure_document_intelligence import AzureDocumentIntelligenceService
from app.services.document_extractor import AzureDocumentExtractor
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
        self.primary_classifier = AzureDocumentIntelligenceClassifier(
            azure_client=self.azure_client,
            classifier_id=self.settings.azure_document_intelligence_classifier_id,
        )
        self.formato_cumplimiento_classifier = (
            AzureDocumentIntelligenceClassifier(
                azure_client=self.azure_client,
                classifier_id=self.settings.azure_document_intelligence_formato_cumplimiento_classifier_id,
            )
            if self.settings.azure_document_intelligence_formato_cumplimiento_classifier_id
            else None
        )
        self.classifier = RoutingDocumentClassifier(
            primary_classifier=self.primary_classifier,
            specialized_classifier=self.formato_cumplimiento_classifier,
            routed_labels={"Formato de cumplimiento"},
        )
        self.extractor = AzureDocumentExtractor(
            azure_client=self.azure_client,
            extraction_models=get_extraction_model_mapping(self.settings),
        )
        self.document_service = DocumentProcessingService(
            classifier=self.classifier,
            extractor=self.extractor,
            repository=self.repository,
            settings=self.settings,
        )


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Return a new dependency container."""
    return Container()
