from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.azure_document_intelligence import AzureDocumentIntelligenceService
from app.utils.azure_parsing import (
    extract_fields_payload,
    extract_layout_tables,
    extract_layout_text_lines,
    resolve_extraction_model_id,
)
from app.utils.errors import ExtractionError


class AzureDocumentExtractor:
    """Resolve an extraction model by label and run it against the full PDF."""

    def __init__(
        self,
        azure_client: AzureDocumentIntelligenceService,
        extraction_models: dict[str, str],
    ) -> None:
        self._azure_client = azure_client
        self._extraction_models = extraction_models

    def extract(self, document_type: str, pdf_path: Path) -> dict[str, Any]:
        model_id = resolve_extraction_model_id(document_type, self._extraction_models)
        if not model_id:
            raise ExtractionError(
                f"No extraction model configured for document type '{document_type}'."
            )

        result = self._azure_client.analyze_document(
            model_id=model_id,
            document_bytes=pdf_path.read_bytes(),
        )
        return extract_fields_payload(result)

    def extract_layout_analysis(self, pdf_path: Path) -> dict[str, Any]:
        """Extract layout tables and OCR lines using Azure prebuilt-layout."""
        result = self._azure_client.analyze_layout(pdf_path.read_bytes())
        return {
            "tables": extract_layout_tables(result),
            "text_lines": extract_layout_text_lines(result),
        }

    def extract_layout_tables(self, pdf_path: Path) -> list[dict[str, Any]]:
        return self.extract_layout_analysis(pdf_path)["tables"]
