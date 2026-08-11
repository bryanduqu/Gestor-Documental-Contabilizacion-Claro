from __future__ import annotations

from app.classifiers.base import DocumentClassifier
from app.schemas.common import ClassificationResult
from app.utils.azure_parsing import normalize_label


class RoutingDocumentClassifier(DocumentClassifier):
    """Route a subset of labels through a specialized classifier."""

    def __init__(
        self,
        primary_classifier: DocumentClassifier,
        specialized_classifier: DocumentClassifier | None,
        routed_labels: set[str],
    ) -> None:
        self._primary_classifier = primary_classifier
        self._specialized_classifier = specialized_classifier
        self._routed_labels = {normalize_label(label) for label in routed_labels}

    def classify(self, first_page_image: bytes) -> ClassificationResult:
        primary_result = self._primary_classifier.classify(first_page_image)
        if self._specialized_classifier is None:
            return primary_result

        if normalize_label(primary_result.type) not in self._routed_labels:
            return primary_result

        return self._specialized_classifier.classify(first_page_image)
