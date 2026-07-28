from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.classifiers.base import DocumentClassifier
from app.repositories.document_repository import InMemoryDocumentRepository
from app.schemas.common import ProcessedDocumentResponse
from app.services.document_extractor import AzureDocumentExtractor
from app.utils.file_utils import save_upload_temporarily
from app.utils.pdf_utils import extract_first_page_image


logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """Orchestrate document classification and structured extraction."""

    def __init__(
        self,
        classifier: DocumentClassifier,
        extractor: AzureDocumentExtractor,
        repository: InMemoryDocumentRepository,
        settings,
    ) -> None:
        self._classifier = classifier
        self._extractor = extractor
        self._repository = repository
        self._settings = settings

    def process(self, upload_file: UploadFile) -> ProcessedDocumentResponse:
        started_at = time.perf_counter()
        pdf_path = save_upload_temporarily(upload_file, self._settings)
        logger.info("Stored temporary file at %s", pdf_path)
        try:
            classification = self._classifier.classify(
                extract_first_page_image(pdf_path)
            )
            extracted_data = self._extractor.extract(classification.type, pdf_path)

            result = ProcessedDocumentResponse(
                id=str(uuid4()),
                document_type=classification.type,
                confidence=classification.confidence,
                data=extracted_data,
                processing_time_ms=int((time.perf_counter() - started_at) * 1000),
                created_at=datetime.now(timezone.utc),
            )
            self._repository.save(result)
            logger.info(
                "Processed document %s as %s",
                result.id,
                result.document_type,
            )
            return result
        finally:
            self._cleanup_temp_file(pdf_path)

    def get_document(self, document_id: str) -> ProcessedDocumentResponse:
        return self._repository.get(document_id)

    @staticmethod
    def _cleanup_temp_file(pdf_path: Path) -> None:
        if pdf_path.exists():
            pdf_path.unlink(missing_ok=True)
