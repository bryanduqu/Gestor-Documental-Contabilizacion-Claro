from __future__ import annotations

import unicodedata
from collections.abc import Mapping
from typing import Any

from app.utils.errors import ClassificationError, ExtractionError


def get_classification_from_result(result: Any) -> tuple[str, float | None]:
    """Extract the top classification from an Azure analyze result."""
    documents = getattr(result, "documents", None) or []
    if not documents:
        raise ClassificationError("Azure classifier returned no document predictions.")

    best_document = max(documents, key=lambda item: getattr(item, "confidence", 0.0) or 0.0)
    raw_doc_type = getattr(best_document, "doc_type", "")
    if not raw_doc_type:
        raise ClassificationError("Azure classifier returned an empty document type.")

    return str(raw_doc_type).strip(), getattr(best_document, "confidence", None)


def normalize_label(value: str) -> str:
    """Normalize labels for resilient matching."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(
        ascii_only.strip().lower().replace("_", " ").replace("-", " ").split()
    )


def resolve_extraction_model_id(
    document_type: str,
    extraction_models: dict[str, str],
) -> str | None:
    """Resolve an extraction model ID from the detected classification label."""
    if document_type in extraction_models:
        return extraction_models[document_type]

    normalized_target = normalize_label(document_type)
    for label, model_id in extraction_models.items():
        if normalize_label(label) == normalized_target:
            return model_id
    return None


def serialize_azure_field(field: Any) -> Any:
    """Convert Azure field values into plain Python data."""
    if field is None:
        return None

    value = getattr(field, "value", None)
    if value is None:
        content = getattr(field, "content", None)
        return content if content not in {"", None} else None

    if isinstance(value, list):
        return [serialize_azure_field(item) for item in value]

    if isinstance(value, Mapping):
        return {str(key): serialize_azure_field(item) for key, item in value.items()}

    if hasattr(value, "items"):
        return {str(key): serialize_azure_field(item) for key, item in value.items()}

    if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool)):
        serialized: dict[str, Any] = {}
        for attr_name, attr_value in vars(value).items():
            if attr_name.startswith("_"):
                continue
            serialized[attr_name] = attr_value
        return serialized or str(value)

    return value


def extract_fields_payload(result: Any) -> dict[str, Any]:
    """Extract fields from Azure analyze result."""
    documents = getattr(result, "documents", None) or []
    if not documents:
        raise ExtractionError("Azure extraction model returned no extracted documents.")

    first_document = documents[0]
    fields = getattr(first_document, "fields", None) or {}
    return {
        str(field_name): serialize_azure_field(field_value)
        for field_name, field_value in fields.items()
    }


def extract_layout_tables(result: Any) -> list[dict[str, Any]]:
    """Extract normalized table data from Azure prebuilt-layout output."""
    tables = getattr(result, "tables", None) or []
    normalized_tables: list[dict[str, Any]] = []

    for table_index, table in enumerate(tables, start=1):
        row_count = int(getattr(table, "row_count", 0) or 0)
        column_count = int(getattr(table, "column_count", 0) or 0)
        matrix = [["" for _ in range(column_count)] for _ in range(row_count)]
        normalized_cells: list[dict[str, Any]] = []

        for cell in getattr(table, "cells", None) or []:
            row_index = int(getattr(cell, "row_index", 0) or 0)
            column_index = int(getattr(cell, "column_index", 0) or 0)
            row_span = int(getattr(cell, "row_span", 1) or 1)
            column_span = int(getattr(cell, "column_span", 1) or 1)
            content = str(getattr(cell, "content", "") or "")
            kind = str(getattr(cell, "kind", "") or "")

            if 0 <= row_index < row_count and 0 <= column_index < column_count:
                matrix[row_index][column_index] = content

            normalized_cells.append(
                {
                    "row_index": row_index,
                    "column_index": column_index,
                    "row_span": row_span,
                    "column_span": column_span,
                    "kind": kind or None,
                    "content": content,
                }
            )

        page_numbers: list[int] = []
        for region in getattr(table, "bounding_regions", None) or []:
            page_number = getattr(region, "page_number", None)
            if isinstance(page_number, int):
                page_numbers.append(page_number)

        header_cells = [
            cell
            for cell in normalized_cells
            if cell.get("kind") in {"columnHeader", "rowHeader", "stubHead", "description"}
        ]
        header_rows = _build_header_rows(header_cells, row_count, column_count)
        header_fields = _build_header_fields(header_cells, row_count, column_count)

        normalized_tables.append(
            {
                "table_index": table_index,
                "row_count": row_count,
                "column_count": column_count,
                "page_numbers": sorted(set(page_numbers)),
                "header_rows": header_rows,
                "header_fields": header_fields,
                "rows": matrix,
                "cells": normalized_cells,
            }
        )

    return normalized_tables


def extract_layout_headers(tables: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a unified header view across all detected layout tables."""
    all_headers: list[str] = []
    header_occurrences: list[dict[str, Any]] = []

    for table in tables:
        for header in table.get("header_fields", []):
            header_text = str(header.get("content", "") or "").strip()
            if not header_text:
                continue

            if header_text not in all_headers:
                all_headers.append(header_text)

            header_occurrences.append(
                {
                    "table_index": table.get("table_index"),
                    "page_numbers": table.get("page_numbers", []),
                    "content": header_text,
                    "merged_label": header.get("merged_label"),
                    "row_index": header.get("row_index"),
                    "column_index": header.get("column_index"),
                    "kind": header.get("kind"),
                }
            )

    return {
        "all_headers": all_headers,
        "header_occurrences": header_occurrences,
    }


def _build_header_rows(
    header_cells: list[dict[str, Any]],
    row_count: int,
    column_count: int,
) -> list[list[str]]:
    """Build a matrix containing only header rows."""
    if not header_cells or row_count <= 0 or column_count <= 0:
        return []

    header_row_indexes = sorted({cell["row_index"] for cell in header_cells})
    header_matrix: list[list[str]] = []
    for row_index in header_row_indexes:
        row_values = ["" for _ in range(column_count)]
        for cell in header_cells:
            if cell["row_index"] != row_index:
                continue
            column_index = int(cell.get("column_index", 0) or 0)
            if 0 <= column_index < column_count:
                row_values[column_index] = str(cell.get("content", "") or "")
        header_matrix.append(row_values)

    return header_matrix


def _build_header_fields(
    header_cells: list[dict[str, Any]],
    row_count: int,
    column_count: int,
) -> list[dict[str, Any]]:
    """Build normalized header field records including merged labels."""
    if not header_cells:
        return []

    header_matrix = [["" for _ in range(column_count)] for _ in range(row_count)]
    for cell in header_cells:
        row_index = int(cell.get("row_index", 0) or 0)
        column_index = int(cell.get("column_index", 0) or 0)
        if 0 <= row_index < row_count and 0 <= column_index < column_count:
            header_matrix[row_index][column_index] = str(cell.get("content", "") or "").strip()

    normalized_headers: list[dict[str, Any]] = []
    for cell in sorted(header_cells, key=lambda item: (item["row_index"], item["column_index"])):
        row_index = int(cell.get("row_index", 0) or 0)
        column_index = int(cell.get("column_index", 0) or 0)
        merged_label_parts: list[str] = []

        for parent_row in range(0, row_index + 1):
            if 0 <= parent_row < row_count and 0 <= column_index < column_count:
                parent_value = header_matrix[parent_row][column_index].strip()
                if parent_value and parent_value not in merged_label_parts:
                    merged_label_parts.append(parent_value)

        normalized_headers.append(
            {
                "content": str(cell.get("content", "") or "").strip(),
                "row_index": row_index,
                "column_index": column_index,
                "row_span": int(cell.get("row_span", 1) or 1),
                "column_span": int(cell.get("column_span", 1) or 1),
                "kind": cell.get("kind"),
                "merged_label": " > ".join(merged_label_parts)
                if merged_label_parts
                else str(cell.get("content", "") or "").strip(),
            }
        )

    return normalized_headers
