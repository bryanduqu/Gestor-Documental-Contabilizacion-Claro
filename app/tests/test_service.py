from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.classifiers.base import DocumentClassifier
from app.repositories.document_repository import InMemoryDocumentRepository
from app.schemas.common import ClassificationResult
from app.services.document_extractor import AzureDocumentExtractor
from app.services.document_processor import DocumentProcessingService
from app.utils.azure_parsing import resolve_extraction_model_id


class DummyClassifier(DocumentClassifier):
    def classify(self, first_page_image: bytes) -> ClassificationResult:
        return ClassificationResult(type="Orden de compra A", confidence=0.99)


class DummySettings:
    temp_dir = Path("/tmp")


class DummyExtractor(AzureDocumentExtractor):
    def __init__(self) -> None:
        pass

    def extract(self, document_type: str, pdf_path: Path) -> dict[str, Any]:
        return {"campo": "valor", "tipo": document_type}

    def extract_layout_tables(self, pdf_path: Path) -> list[dict[str, Any]]:
        return [
            {
                "table_index": 1,
                "row_count": 2,
                "column_count": 2,
                "page_numbers": [1],
                "header_rows": [["Header A", "Header B"]],
                "header_fields": [
                    {
                        "content": "Header A",
                        "row_index": 0,
                        "column_index": 0,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Header A",
                    },
                    {
                        "content": "Header B",
                        "row_index": 0,
                        "column_index": 1,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Header B",
                    },
                ],
                "rows": [["Header A", "Header B"], ["A", "B"]],
                "cells": [],
            }
        ]


def test_document_processing_service(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.document_processor.save_upload_temporarily",
        lambda upload_file, settings: Path("/tmp/fake.pdf"),
    )
    monkeypatch.setattr(
        "app.services.document_processor.extract_first_page_image",
        lambda pdf_path: b"image",
    )
    monkeypatch.setattr(
        "app.services.document_processor.DocumentProcessingService._cleanup_temp_file",
        lambda self, pdf_path: None,
    )

    service = DocumentProcessingService(
        classifier=DummyClassifier(),
        extractor=DummyExtractor(),
        repository=InMemoryDocumentRepository(),
        settings=DummySettings(),
    )

    upload = UploadFile(filename="test.pdf", file=BytesIO(b"%PDF-1.4"))
    result = service.process(upload)

    assert result.document_type == "Orden de compra A"
    assert result.data["campo"] == "valor"
    assert result.layout_tables[0]["rows"][1][0] == "A"
    assert "Header A" in result.layout_headers["all_headers"]
    assert service.get_document(result.id).id == result.id


def test_resolve_extraction_model_id_ignores_accents() -> None:
    extraction_models = {
        "Entrada de mercancía": "modelo_em",
    }

    assert (
        resolve_extraction_model_id("Entrada de Mercancia", extraction_models)
        == "modelo_em"
    )
