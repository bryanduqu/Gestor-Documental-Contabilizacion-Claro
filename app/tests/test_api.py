from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient

from app.backend.api import create_app
from app.backend.dependencies.container import get_container
from app.schemas.common import ProcessedDocumentResponse


class FakeDocumentService:
    def __init__(self) -> None:
        self.document = ProcessedDocumentResponse(
            id="doc-1",
            document_type="Formato de cumplimiento",
            confidence=0.98,
            data={"campo": "valor"},
            layout_tables=[{"table_index": 1, "row_count": 1, "column_count": 1, "page_numbers": [1], "rows": [["X"]], "cells": []}],
            layout_headers={"all_headers": ["Header X"], "header_occurrences": [{"table_index": 1, "page_numbers": [1], "content": "Header X", "merged_label": "Header X", "row_index": 0, "column_index": 0, "kind": "columnHeader"}]},
            processing_time_ms=42,
            created_at="2026-07-28T00:00:00Z",
        )

    def process(self, upload_file):
        return self.document

    def get_document(self, document_id: str):
        return self.document


class FakeContainer:
    def __init__(self) -> None:
        self.document_service = FakeDocumentService()


def test_upload_endpoint_returns_processed_document() -> None:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: FakeContainer()
    client = TestClient(app)

    response = client.post(
        "/upload",
        files={"file": ("doc.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["document_type"] == "Formato de cumplimiento"


def test_get_document_endpoint_returns_processed_document() -> None:
    app = create_app()
    app.dependency_overrides[get_container] = lambda: FakeContainer()
    client = TestClient(app)

    response = client.get("/document/doc-1")

    assert response.status_code == 200
    assert response.json()["id"] == "doc-1"
