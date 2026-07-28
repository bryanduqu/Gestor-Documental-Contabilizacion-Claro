from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import UploadFile

from app.classifiers.base import DocumentClassifier
from app.repositories.document_repository import InMemoryDocumentRepository
from app.schemas.common import ClassificationResult
from app.services.document_processor import DocumentProcessingService


class DummyClassifier(DocumentClassifier):
    def classify(self, first_page_image: bytes) -> ClassificationResult:
        return ClassificationResult(type="Orden de compra A", confidence=0.99)


class DummySettings:
    temp_dir = Path("/tmp")


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
        repository=InMemoryDocumentRepository(),
        settings=DummySettings(),
    )

    upload = UploadFile(filename="test.pdf", file=BytesIO(b"%PDF-1.4"))
    result = service.process(upload)

    assert result.document_type == "Orden de compra A"
    assert service.get_document(result.id).id == result.id
