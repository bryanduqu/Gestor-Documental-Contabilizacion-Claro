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
    assert service.get_document(result.id).id == result.id
