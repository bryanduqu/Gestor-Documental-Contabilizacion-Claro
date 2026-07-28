from __future__ import annotations

import logging

from app.classifiers.base import DocumentClassifier
from app.schemas.common import ClassificationResult
from app.services.azure_document_intelligence import AzureDocumentIntelligenceService
from app.utils.azure_parsing import get_classification_from_result
from app.utils.errors import ClassificationError


logger = logging.getLogger(__name__)


class AzureDocumentIntelligenceClassifier(DocumentClassifier):
    """Azure Document Intelligence classifier using the first page image."""

    def __init__(
        self,
        azure_client: AzureDocumentIntelligenceService,
        classifier_id: str,
    ) -> None:
        self._azure_client = azure_client
        self._classifier_id = classifier_id

    def classify(self, first_page_image: bytes) -> ClassificationResult:
        if not self._classifier_id:
            raise ClassificationError(
                "AZURE_DOCUMENT_INTELLIGENCE_CLASSIFIER_ID is not configured."
            )

        result = self._azure_client.classify_first_page(
            classifier_id=self._classifier_id,
            image_bytes=first_page_image,
        )
        document_type, confidence = get_classification_from_result(result)

        classification = ClassificationResult(
            type=document_type,
            confidence=confidence,
        )
        logger.info("Document classified as %s", classification.type)
        return classification
