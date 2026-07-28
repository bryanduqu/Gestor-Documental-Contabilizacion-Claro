from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.common import ClassificationResult


class DocumentClassifier(ABC):
    """Common interface for document classifiers."""

    @abstractmethod
    def classify(self, first_page_image: bytes) -> ClassificationResult:
        """Classify a document using the first page image."""
