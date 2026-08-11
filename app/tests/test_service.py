from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.classifiers.base import DocumentClassifier
from app.classifiers.routing_classifier import RoutingDocumentClassifier
from app.repositories.document_repository import InMemoryDocumentRepository
from app.schemas.common import ClassificationResult
from app.services.document_extractor import AzureDocumentExtractor
from app.services.document_processor import DocumentProcessingService
from app.utils.azure_parsing import (
    extract_line_items_table,
    extract_totals_summary,
    resolve_extraction_model_id,
)


class DummyClassifier(DocumentClassifier):
    def classify(self, first_page_image: bytes) -> ClassificationResult:
        return ClassificationResult(type="Entrada de Mercancia", confidence=0.99)


class SequenceClassifier(DocumentClassifier):
    def __init__(self, result_type: str, confidence: float) -> None:
        self.result_type = result_type
        self.confidence = confidence
        self.calls = 0

    def classify(self, first_page_image: bytes) -> ClassificationResult:
        self.calls += 1
        return ClassificationResult(type=self.result_type, confidence=self.confidence)


class DummySettings:
    temp_dir = Path("/tmp")


class DummyExtractor(AzureDocumentExtractor):
    def __init__(self) -> None:
        pass

    def extract(self, document_type: str, pdf_path: Path) -> dict[str, Any]:
        return {"campo": "valor", "tipo": document_type, "total_bruto": "578.076.994,00 COP", "iva": "0 COP"}

    def extract_layout_analysis(self, pdf_path: Path) -> dict[str, Any]:
        return {"tables": [
            {
                "table_index": 1,
                "row_count": 3,
                "column_count": 10,
                "page_numbers": [1],
                "header_rows": [[
                    "Pos.",
                    "Material",
                    "Desc. Material",
                    "Pos. Pedido",
                    "UMB",
                    "Centro",
                    "Almacén",
                    "Cant.",
                    "Unitario",
                    "TOTAL",
                ]],
                "header_fields": [
                    {
                        "content": "Pos.",
                        "row_index": 0,
                        "column_index": 0,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Pos.",
                    },
                    {
                        "content": "Material",
                        "row_index": 0,
                        "column_index": 1,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Material",
                    },
                    {
                        "content": "Desc. Material",
                        "row_index": 0,
                        "column_index": 2,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Desc. Material",
                    },
                    {
                        "content": "Pos. Pedido",
                        "row_index": 0,
                        "column_index": 3,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Pos. Pedido",
                    },
                    {
                        "content": "UMB",
                        "row_index": 0,
                        "column_index": 4,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "UMB",
                    },
                    {
                        "content": "Centro",
                        "row_index": 0,
                        "column_index": 5,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Centro",
                    },
                    {
                        "content": "Almacén",
                        "row_index": 0,
                        "column_index": 6,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Almacén",
                    },
                    {
                        "content": "Cant.",
                        "row_index": 0,
                        "column_index": 7,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Cant.",
                    },
                    {
                        "content": "Unitario",
                        "row_index": 0,
                        "column_index": 8,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "Unitario",
                    },
                    {
                        "content": "TOTAL",
                        "row_index": 0,
                        "column_index": 9,
                        "row_span": 1,
                        "column_span": 1,
                        "kind": "columnHeader",
                        "merged_label": "TOTAL",
                    },
                ],
                "rows": [
                    ["Pos.", "Material", "Desc. Material", "Pos. Pedido", "UMB", "Centro", "Almacén", "Cant.", "Unitario", "TOTAL"],
                    ["1", "1064535", "SRV INSTALACION", "110", "SRV", "C004", "P008", "9,00", "63.119.666,00", "568.076.994,00"],
                    ["2", "1064536", "SRV INTEGRACION", "120", "SRV", "C004", "P008", "1,00", "10.000,00", "10.000,00"],
                ],
                "cells": [],
            },
            {
                "table_index": 2,
                "row_count": 2,
                "column_count": 2,
                "page_numbers": [1],
                "header_rows": [["Otra", "Tabla"]],
                "header_fields": [
                    {"content": "Otra", "row_index": 0, "column_index": 0, "row_span": 1, "column_span": 1, "kind": "columnHeader", "merged_label": "Otra"},
                    {"content": "Tabla", "row_index": 0, "column_index": 1, "row_span": 1, "column_span": 1, "kind": "columnHeader", "merged_label": "Tabla"},
                ],
                "rows": [["Otra", "Tabla"], ["X", "Y"]],
                "cells": [],
            },
        ], "text_lines": ["578.076.994,00 COP", "Total Bruto"]}


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

    assert result.document_type == "Entrada de Mercancia"
    assert result.data["campo"] == "valor"
    assert result.layout_tables[0]["rows"][1][0] == "1"
    assert "Material" in result.layout_headers["all_headers"]
    assert result.line_items_table["rows"][0][1] == "1064535"
    assert result.line_items_table["source_table_indexes"] == [1]
    assert result.totals_summary["total_bruto"] == "578.076.994,00 COP"
    assert service.get_document(result.id).id == result.id


def test_routing_classifier_uses_specialized_classifier_for_formato_cumplimiento() -> None:
    primary = SequenceClassifier("Formato de cumplimiento", 0.82)
    specialized = SequenceClassifier("Formato de cumplimiento USD", 0.91)
    classifier = RoutingDocumentClassifier(
        primary_classifier=primary,
        specialized_classifier=specialized,
        routed_labels={"Formato de cumplimiento"},
    )

    result = classifier.classify(b"image")

    assert result.type == "Formato de cumplimiento USD"
    assert result.confidence == 0.91
    assert primary.calls == 1
    assert specialized.calls == 1


def test_routing_classifier_keeps_primary_result_for_non_routed_labels() -> None:
    primary = SequenceClassifier("Orden de compra A", 0.97)
    specialized = SequenceClassifier("Formato de cumplimiento USD", 0.91)
    classifier = RoutingDocumentClassifier(
        primary_classifier=primary,
        specialized_classifier=specialized,
        routed_labels={"Formato de cumplimiento"},
    )

    result = classifier.classify(b"image")

    assert result.type == "Orden de compra A"
    assert result.confidence == 0.97
    assert primary.calls == 1
    assert specialized.calls == 0


def test_resolve_extraction_model_id_ignores_accents() -> None:
    extraction_models = {
        "Entrada de mercancía": "modelo_em",
    }

    assert (
        resolve_extraction_model_id("Entrada de Mercancia", extraction_models)
        == "modelo_em"
    )


def test_extract_line_items_table_for_supported_documents() -> None:
    tables = [
        {
            "table_index": 1,
            "page_numbers": [1],
            "header_rows": [["Pos.Mat./Serv.", "Descripción", "UMB", "Ctro", "Alm.", "En pedido", "Recibida", "Unitario", "Total"]],
            "header_fields": [
                {"content": "Pos.Mat./Serv.", "column_index": 0, "merged_label": "Pos.Mat./Serv."},
                {"content": "Descripción", "column_index": 1, "merged_label": "Descripción"},
                {"content": "UMB", "column_index": 2, "merged_label": "UMB"},
                {"content": "Ctro", "column_index": 3, "merged_label": "Ctro"},
                {"content": "Alm.", "column_index": 4, "merged_label": "Alm."},
                {"content": "En pedido", "column_index": 5, "merged_label": "En pedido"},
                {"content": "Recibida", "column_index": 6, "merged_label": "Recibida"},
                {"content": "Unitario", "column_index": 7, "merged_label": "Unitario"},
                {"content": "Total", "column_index": 8, "merged_label": "Total"},
            ],
            "rows": [
                ["Pos.Mat./Serv.", "Descripción", "UMB", "Ctro", "Alm.", "En pedido", "Recibida", "Unitario", "Total"],
                ["10", "SRV SOPORTE", "SRV", "C015", "", "1,00", "1,00", "518.386.176,00", "518.386.176,00"],
            ],
        }
    ]

    result = extract_line_items_table("Formato de cumplimiento", tables)

    assert result["canonical_headers"][0] == "pos"
    assert len(result["headers"]) == 9
    assert result["normalized_rows"][0]["descripcion"] == "SRV SOPORTE"
    assert result["normalized_rows"][0]["cantidad"] == "1,00"


def test_extract_line_items_table_for_purchase_order_b() -> None:
    tables = [
        {
            "table_index": 1,
            "page_numbers": [2],
            "header_rows": [[
                "Partida Item",
                "No. Requisición Requisition Number",
                "Código (No. de catálogo) Code (Catalogue)",
                "Descripción de los bienes Description",
                "Programa de entregas",
                "Mes Month",
                "Dia Day",
                "Año Year",
                "Cantidad Quantity",
                "Unidad Unit",
                "Centro/Alm Plant/Store",
                "Precio unitario Bruto Brute Unit Price",
                "Descuento Recargo Gastos de Prov.",
                "Valor Bruto Brute Total Price",
            ]],
            "header_fields": [
                {"content": "Partida Item", "column_index": 0, "merged_label": "Partida Item"},
                {"content": "No. Requisición Requisition Number", "column_index": 1, "merged_label": "No. Requisición Requisition Number"},
                {"content": "Código (No. de catálogo) Code (Catalogue)", "column_index": 2, "merged_label": "Código (No. de catálogo) Code (Catalogue)"},
                {"content": "Descripción de los bienes Description", "column_index": 3, "merged_label": "Descripción de los bienes Description"},
                {"content": "Programa de entregas", "column_index": 4, "merged_label": "Programa de entregas"},
                {"content": "Mes Month", "column_index": 5, "merged_label": "Mes Month"},
                {"content": "Dia Day", "column_index": 6, "merged_label": "Dia Day"},
                {"content": "Año Year", "column_index": 7, "merged_label": "Año Year"},
                {"content": "Cantidad Quantity", "column_index": 8, "merged_label": "Cantidad Quantity"},
                {"content": "Unidad Unit", "column_index": 9, "merged_label": "Unidad Unit"},
                {"content": "Centro/Alm Plant/Store", "column_index": 10, "merged_label": "Centro/Alm Plant/Store"},
                {"content": "Precio unitario Bruto Brute Unit Price", "column_index": 11, "merged_label": "Precio unitario Bruto Brute Unit Price"},
                {"content": "Descuento Recargo Gastos de Prov.", "column_index": 12, "merged_label": "Descuento Recargo Gastos de Prov."},
                {"content": "Valor Bruto Brute Total Price", "column_index": 13, "merged_label": "Valor Bruto Brute Total Price"},
            ],
            "rows": [
                [
                    "Partida Item",
                    "No. Requisición Requisition Number",
                    "Código (No. de catálogo) Code (Catalogue)",
                    "Descripción de los bienes Description",
                    "Programa de entregas",
                    "Mes Month",
                    "Dia Day",
                    "Año Year",
                    "Cantidad Quantity",
                    "Unidad Unit",
                    "Centro/Alm Plant/Store",
                    "Precio unitario Bruto Brute Unit Price",
                    "Descuento Recargo Gastos de Prov.",
                    "Valor Bruto Brute Total Price",
                ],
                [
                    "00010",
                    "10944754/10",
                    "4041983",
                    "RECTIFICADOR E62753034/201",
                    "1 - 10 9B2DCB-0DFA22",
                    "12",
                    "12",
                    "2025",
                    "1,00",
                    "PZA",
                    "C004 / P008",
                    "91.000.000",
                    "0",
                    "91.000.000",
                ],
                ["434.178.595 COP"],
                ["Total Efectivo"],
                ["69.322.633 COP"],
                ["Iva:"],
                ["0 COP"],
                ["Descuento:"],
                ["364.855.962 COP"],
                ["Neto:"],
                ["434.178.595 COP"],
                ["Total Bruto"],
            ],
        }
    ]

    result = extract_line_items_table("Orden de compra B", tables)
    totals = extract_totals_summary("Orden de compra B", {}, tables)

    assert len(result["headers"]) == 13
    assert result["normalized_rows"][0]["item"] == "00010"
    assert result["normalized_rows"][0]["requisicion"] == "10944754/10"
    assert result["normalized_rows"][0]["codigo_catalogo"] == "4041983"
    assert totals["total_efectivo"] == "434.178.595 COP"
    assert totals["iva"] == "69.322.633 COP"
    assert totals["descuento"] == "0 COP"
    assert totals["neto"] == "364.855.962 COP"
    assert totals["total_bruto"] == "434.178.595 COP"


def test_extract_line_items_table_for_purchase_order_a() -> None:
    tables = [
        {
            "table_index": 1,
            "page_numbers": [1],
            "header_rows": [[
                "Partida Item",
                "No. Requisición",
                "Código (No. de catálogo)",
                "Descripción de los bienes",
                "Texto Corto posición",
                "Programa de entregas",
                "Cantidad",
                "Unidad",
                "Centro/Alm",
                "Precio unitario Bruto Brute",
                "Descuento Recargo Gastos de Prov",
                "Valor Bruto Brute Total",
            ]],
            "header_fields": [
                {"content": "Partida Item", "column_index": 0, "merged_label": "Partida Item"},
                {"content": "No. Requisición", "column_index": 1, "merged_label": "No. Requisición"},
                {"content": "Código (No. de catálogo)", "column_index": 2, "merged_label": "Código (No. de catálogo)"},
                {"content": "Descripción de los bienes", "column_index": 3, "merged_label": "Descripción de los bienes"},
                {"content": "Texto Corto posición", "column_index": 4, "merged_label": "Texto Corto posición"},
                {"content": "Programa de entregas", "column_index": 5, "merged_label": "Programa de entregas"},
                {"content": "Cantidad", "column_index": 6, "merged_label": "Cantidad"},
                {"content": "Unidad", "column_index": 7, "merged_label": "Unidad"},
                {"content": "Centro/Alm", "column_index": 8, "merged_label": "Centro/Alm"},
                {"content": "Precio unitario Bruto Brute", "column_index": 9, "merged_label": "Precio unitario Bruto Brute"},
                {"content": "Descuento Recargo Gastos de Prov", "column_index": 10, "merged_label": "Descuento Recargo Gastos de Prov"},
                {"content": "Valor Bruto Brute Total", "column_index": 11, "merged_label": "Valor Bruto Brute Total"},
            ],
            "rows": [
                [
                    "Partida Item",
                    "No. Requisición",
                    "Código (No. de catálogo)",
                    "Descripción de los bienes",
                    "Texto Corto posición",
                    "Programa de entregas",
                    "Cantidad",
                    "Unidad",
                    "Centro/Alm",
                    "Precio unitario Bruto Brute",
                    "Descuento Recargo Gastos de Prov",
                    "Valor Bruto Brute Total",
                ],
                [
                    "10",
                    "REQ060465",
                    "3027229",
                    "SRV IMPLEMENTACION DESMONTE BTS",
                    "SRV IMPLEMENTACION DESMONTE BTS",
                    "6/19/2026",
                    "1.00",
                    "SRV",
                    "C015/",
                    "1,679,610.00",
                    "",
                    "1,998,735.90",
                ],
                ["Total Bruto:", "3,096,694.00 COP"],
                ["Iva:", "588,371.86 COP"],
                ["Total Efectivo:", "3,685,065.86 COP"],
            ],
        }
    ]

    result = extract_line_items_table("Orden de compra A", tables)
    totals = extract_totals_summary("Orden de compra A", {}, tables)

    assert len(result["headers"]) == 12
    assert result["normalized_rows"][0]["item"] == "10"
    assert result["normalized_rows"][0]["requisicion"] == "REQ060465"
    assert result["normalized_rows"][0]["texto_corto_posicion"] == "SRV IMPLEMENTACION DESMONTE BTS"
    assert result["normalized_rows"][0]["fecha_entrega"] == "6/19/2026"
    assert result["normalized_rows"][0]["unitario"] == "1,679,610.00"
    assert totals["total_bruto"] == "3,096,694.00 COP"
    assert totals["iva"] == "588,371.86 COP"
    assert totals["total_efectivo"] == "3,685,065.86 COP"


def test_extract_line_items_table_merges_entrada_de_mercancia_continuation_tables() -> None:
    tables = [
        {
            "table_index": 1,
            "page_numbers": [1],
            "header_rows": [[
                "Pos.",
                "Material",
                "Desc. Material",
                "Pos. Pedido",
                "UMB",
                "Centro",
                "Almacén",
                "Cant.",
                "Unitario",
                "TOTAL",
            ]],
            "header_fields": [
                {"content": "Pos.", "column_index": 0, "merged_label": "Pos."},
                {"content": "Material", "column_index": 1, "merged_label": "Material"},
                {"content": "Desc. Material", "column_index": 2, "merged_label": "Desc. Material"},
                {"content": "Pos. Pedido", "column_index": 3, "merged_label": "Pos. Pedido"},
                {"content": "UMB", "column_index": 4, "merged_label": "UMB"},
                {"content": "Centro", "column_index": 5, "merged_label": "Centro"},
                {"content": "Almacén", "column_index": 6, "merged_label": "Almacén"},
                {"content": "Cant.", "column_index": 7, "merged_label": "Cant."},
                {"content": "Unitario", "column_index": 8, "merged_label": "Unitario"},
                {"content": "TOTAL", "column_index": 9, "merged_label": "TOTAL"},
            ],
            "rows": [
                ["Pos.", "Material", "Desc. Material", "Pos. Pedido", "UMB", "Centro", "Almacén", "Cant.", "Unitario", "TOTAL"],
                ["1", "1064535", "SRV INSTALACION", "110", "SRV", "C004", "P008", "9,00", "63.119.666,00", "568.076.994,00"],
            ],
        },
        {
            "table_index": 2,
            "page_numbers": [2],
            "header_rows": [],
            "header_fields": [],
            "rows": [
                ["2", "1064536", "SRV INTEGRACION", "120", "SRV", "C004", "P008", "1,00", "10.000,00", "10.000,00"],
                ["3", "1064537", "SRV SOPORTE", "130", "SRV", "C004", "P008", "2,00", "20.000,00", "40.000,00"],
            ],
        },
    ]

    result = extract_line_items_table("Entrada de Mercancia", tables)

    assert [row[0] for row in result["rows"]] == ["1", "2", "3"]
    assert result["source_table_indexes"] == [1, 2]
    assert result["page_numbers"] == [1, 2]
