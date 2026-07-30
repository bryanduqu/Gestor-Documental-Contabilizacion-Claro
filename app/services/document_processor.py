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
from app.utils.azure_parsing import (
    extract_layout_headers,
    extract_line_items_table,
    extract_totals_summary,
)
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
            layout_analysis = self._extractor.extract_layout_analysis(pdf_path)
            layout_tables = layout_analysis.get("tables", [])
            layout_text_lines = layout_analysis.get("text_lines", [])
            layout_headers = extract_layout_headers(layout_tables)
            line_items_table = extract_line_items_table(
                classification.type,
                layout_tables,
            )
            totals_summary = extract_totals_summary(
                classification.type,
                extracted_data,
                layout_tables,
                layout_text_lines,
            )

            result = ProcessedDocumentResponse(
                id=str(uuid4()),
                document_type=classification.type,
                confidence=classification.confidence,
                data=extracted_data,
                layout_tables=layout_tables,
                layout_headers=layout_headers,
                line_items_table=line_items_table,
                totals_summary=totals_summary,
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
