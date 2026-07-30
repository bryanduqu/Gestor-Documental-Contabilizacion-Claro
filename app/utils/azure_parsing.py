from __future__ import annotations

import re
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


LINE_ITEM_DOCUMENT_PROFILES = {
    normalize_label("Entrada de mercancia"): {
        "columns": [
            "pos",
            "material",
            "descripcion",
            "pos_pedido",
            "umb",
            "centro",
            "almacen",
            "cantidad",
            "unitario",
            "total",
        ],
        "headers": [
            "Pos.",
            "Material",
            "Desc. Material",
            "Pos. Pedido",
            "UMB",
            "Centro",
            "Almacen",
            "Cantidad",
            "Unitario",
            "Total",
        ],
    },
    normalize_label("Formato de cumplimiento"): {
        "columns": [
            "pos",
            "descripcion",
            "umb",
            "centro",
            "almacen",
            "cantidad",
            "recibida",
            "unitario",
            "total",
        ],
        "headers": [
            "Pos.Mat./Serv.",
            "Descripcion",
            "UMB",
            "Ctro",
            "Alm.",
            "En pedido",
            "Recibida",
            "Unitario",
            "Total",
        ],
    },
    normalize_label("Orden de compra A"): {
        "columns": [
            "item",
            "requisicion",
            "codigo_catalogo",
            "descripcion",
            "texto_corto_posicion",
            "fecha_entrega",
            "cantidad",
            "umb",
            "centro_almacen",
            "unitario",
            "descuento_recargo",
            "total",
        ],
        "headers": [
            "Partida Item",
            "No. Requisicion",
            "Codigo (No. de catalogo)",
            "Descripcion de los bienes",
            "Texto Corto posicion",
            "Programa de entregas",
            "Cantidad",
            "Unidad",
            "Centro/Alm",
            "Precio unitario Bruto",
            "Descuento Recargo Gastos de Prov.",
            "Valor Bruto",
        ],
    },
    normalize_label("Orden de compra B"): {
        "columns": [
            "item",
            "requisicion",
            "codigo_catalogo",
            "descripcion",
            "mes",
            "dia",
            "ano",
            "cantidad",
            "umb",
            "centro_almacen",
            "unitario",
            "descuento_recargo",
            "total",
        ],
        "headers": [
            "Partida Item",
            "No. Requisicion",
            "Codigo (No. de catalogo)",
            "Descripcion de los bienes",
            "Mes",
            "Dia",
            "Ano",
            "Cantidad",
            "Unidad",
            "Centro/Alm",
            "Precio unitario Bruto",
            "Descuento Recargo Gastos de Prov.",
            "Valor Bruto",
        ],
    },
}

LINE_ITEM_HEADER_ALIASES = {
    "pos": {"pos", "pos.", "pos.mat./serv.", "pos mat./serv.", "pos.mat./serv"},
    "item": {"item", "partida item", "partida"},
    "requisicion": {
        "no. requisicion",
        "no requisicion",
        "requisition number",
        "requisicion",
    },
    "codigo_catalogo": {
        "codigo",
        "codigo no. de catalogo",
        "codigo no de catalogo",
        "code catalogue",
        "catalogue",
        "catalogo",
    },
    "material": {"material", "mat./serv.", "mat./serv", "mat", "serv"},
    "descripcion": {
        "desc. material",
        "descripcion",
        "descripción",
        "desc material",
        "descripcion de los bienes",
        "description",
    },
    "texto_corto_posicion": {"texto corto posicion"},
    "programa_entregas": {"programa de entregas"},
    "fecha_entrega": {
        "delivery date",
        "fecha entrega",
        "programa de entregas",
    },
    "pos_pedido": {"pos. pedido", "pos pedido", "pedido"},
    "umb": {"umb", "unidad", "unit"},
    "centro": {"centro", "ctro", "plant/store", "plant"},
    "almacen": {"almacen", "almacén", "alm.", "alm"},
    "centro_almacen": {"centro/alm", "centro alm", "plant/store", "centro/alm plant/store"},
    "mes": {"mes", "month"},
    "dia": {"dia", "day"},
    "ano": {"ano", "año", "year"},
    "cantidad": {"cant.", "cant", "cantidad", "quantity", "en pedido"},
    "recibida": {"recibida"},
    "unitario": {"unitario", "precio unitario bruto", "brute unit price", "precio unitario bruto brute"},
    "descuento_recargo": {
        "descuento",
        "recargo",
        "gastos de prov.",
        "descuento recargo gastos de prov.",
    },
    "total": {"total", "valor bruto", "brute total price", "valor bruto brute total"},
}

REQUIRED_LINE_ITEM_COLUMNS_BY_DOCUMENT = {
    normalize_label("Orden de compra A"): {
        "item",
        "requisicion",
        "codigo_catalogo",
        "descripcion",
        "cantidad",
        "umb",
        "centro_almacen",
        "unitario",
        "total",
    },
}

TOTAL_KEY_ALIASES = {
    "total_bruto": {"total bruto", "valor bruto", "brute total price"},
    "descuento": {"descuento", "discount"},
    "iva": {"iva"},
    "neto": {"neto", "subtotal"},
    "total_efectivo": {"total efectivo", "cash total"},
}

TOTALS_SUPPORTED_DOCUMENT_TYPES = {
    normalize_label("Orden de compra A"),
    normalize_label("Orden de compra B"),
}

AMOUNT_PATTERN = re.compile(
    r"^(?:USD|COP)?\s*[0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?\s*(?:USD|COP)?$",
    re.IGNORECASE,
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


def extract_layout_text_lines(result: Any) -> list[str]:
    """Extract OCR text lines from Azure prebuilt-layout output."""
    lines: list[str] = []
    for page in getattr(result, "pages", None) or []:
        for line in getattr(page, "lines", None) or []:
            content = str(getattr(line, "content", "") or "").strip()
            if content:
                lines.append(content)
    return lines


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


def extract_line_items_table(
    document_type: str,
    tables: list[dict[str, Any]],
) -> dict[str, Any]:
    """Extract a single consolidated items table for supported document types."""
    normalized_document_type = normalize_label(document_type)
    profile = LINE_ITEM_DOCUMENT_PROFILES.get(normalized_document_type)
    if not profile:
        return {}

    canonical_columns = profile["columns"]

    if normalized_document_type == normalize_label("Orden de compra A"):
        return _extract_purchase_order_a_table(tables, profile["headers"], canonical_columns)

    matched_tables: list[dict[str, Any]] = []
    merged_rows: list[list[str]] = []
    pages: list[int] = []
    last_valid_header_map: dict[str, int] | None = None

    for table in tables:
        header_map = _resolve_line_item_header_map(
            table,
            canonical_columns,
            LINE_ITEM_HEADER_ALIASES,
        )
        required_columns = REQUIRED_LINE_ITEM_COLUMNS_BY_DOCUMENT.get(
            normalized_document_type
        )
        use_inherited_header_map = False

        if required_columns:
            if not required_columns.issubset(set(header_map.keys())):
                continue
        elif len(header_map) < max(4, min(5, len(canonical_columns))):
            if (
                normalized_document_type == normalize_label("Entrada de mercancia")
                and last_valid_header_map
                and _is_continuation_table(table, last_valid_header_map)
            ):
                header_map = last_valid_header_map
                use_inherited_header_map = True
            else:
                continue
        else:
            last_valid_header_map = header_map

        if not use_inherited_header_map:
            last_valid_header_map = header_map

        matched_tables.append(
            {
                "table_index": table.get("table_index"),
                "matched_headers": sorted(header_map.keys()),
            }
        )
        pages.extend(table.get("page_numbers", []))

        candidate_rows = _extract_table_data_rows(table)
        if use_inherited_header_map and not table.get("header_rows"):
            candidate_rows = table.get("rows") or []

        for row in candidate_rows:
            if _is_totals_row(row):
                continue
            if not _is_line_item_row(row, header_map):
                continue

            normalized_row = []
            for column_name in canonical_columns:
                source_index = header_map.get(column_name)
                value = row[source_index].strip() if source_index is not None and source_index < len(row) else ""
                normalized_row.append(value)

            if any(normalized_row):
                merged_rows.append(normalized_row)

    if not merged_rows:
        return {}

    normalized_rows = [
        {column_name: row[index] for index, column_name in enumerate(canonical_columns)}
        for row in merged_rows
    ]

    return {
        "headers": profile["headers"],
        "canonical_headers": canonical_columns,
        "rows": merged_rows,
        "normalized_rows": normalized_rows,
        "source_table_indexes": [
            table["table_index"] for table in matched_tables if table.get("table_index") is not None
        ],
        "page_numbers": sorted(set(page for page in pages if isinstance(page, int))),
    }


def extract_totals_summary(
    document_type: str,
    extracted_data: dict[str, Any],
    tables: list[dict[str, Any]],
    layout_text_lines: list[str] | None = None,
) -> dict[str, Any]:
    """Extract totals summary for supported commercial documents."""
    if normalize_label(document_type) not in TOTALS_SUPPORTED_DOCUMENT_TYPES:
        return {}

    totals: dict[str, Any] = {}

    if layout_text_lines:
        line_totals = _extract_totals_from_lines(layout_text_lines)
        totals.update({key: value for key, value in line_totals.items() if _looks_like_amount(str(value))})
        if len(totals) == 5:
            return totals

    layout_totals = _extract_totals_from_tables(tables)
    totals.update({key: value for key, value in layout_totals.items() if _looks_like_amount(str(value))})
    if len(totals) == 5:
        return totals

    payload_totals = _extract_totals_from_payload(extracted_data)
    totals.update({key: value for key, value in payload_totals.items() if _looks_like_amount(str(value))})
    return totals


def _extract_totals_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    for field, value in flatten_totals_payload(payload):
        normalized_field = normalize_label(field.replace(":", " "))
        total_key = _resolve_total_key(normalized_field)
        if total_key and value not in (None, "", [], {}):
            totals[total_key] = value
    return totals


def flatten_totals_payload(payload: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    for key, value in payload.items():
        full_key = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            rows.extend(flatten_totals_payload(value, full_key))
        else:
            rows.append((full_key, value))
    return rows


def _extract_totals_from_lines(lines: list[str]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    footer_amounts: list[str] = []
    footer_labels: list[str] = []

    for raw_line in lines[-60:]:
        line = str(raw_line).strip()
        if not line:
            continue
        total_key = _resolve_total_key(line)
        if total_key:
            footer_labels.append(total_key)
            continue
        if _looks_like_amount(line):
            footer_amounts.append(line)

    if len(footer_amounts) >= 5:
        amount_block = footer_amounts[-5:]
        # In purchase orders the footer amounts are emitted before the labels
        # in this visual order: Total Efectivo, Neto, IVA, Descuento, Total Bruto.
        totals.update(
            {
                "total_efectivo": amount_block[0],
                "neto": amount_block[1],
                "iva": amount_block[2],
                "descuento": amount_block[3],
                "total_bruto": amount_block[4],
            }
        )
        return totals

    if footer_labels and footer_amounts and len(footer_amounts) >= len(footer_labels):
        amount_block = footer_amounts[-len(footer_labels):]
        for label, amount in zip(footer_labels, amount_block):
            totals[label] = amount

    return totals


def _extract_totals_from_tables(tables: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {}
    flattened_rows = [row for table in tables for row in table.get("rows", [])]

    footer_amounts: list[str] = []
    footer_labels: list[str] = []
    for row in flattened_rows:
        non_empty_cells = [str(cell).strip() for cell in row if str(cell).strip()]
        if not non_empty_cells:
            continue

        if len(non_empty_cells) == 1:
            cell = non_empty_cells[0]
            total_key = _resolve_total_key(cell)
            if total_key:
                footer_labels.append(total_key)
                continue
            if _looks_like_amount(cell):
                footer_amounts.append(cell)
                continue

        total_labels = [_resolve_total_key(cell) for cell in non_empty_cells]
        total_labels = [label for label in total_labels if label]
        amount_in_row = _find_amount_in_row(row)
        if total_labels and amount_in_row:
            totals[total_labels[0]] = amount_in_row

    if len(footer_amounts) >= 5:
        totals.update(
            {
                "total_efectivo": footer_amounts[0],
                "iva": footer_amounts[1],
                "descuento": footer_amounts[2],
                "neto": footer_amounts[3],
                "total_bruto": footer_amounts[4],
            }
        )
    elif footer_amounts and footer_labels and len(footer_amounts) == len(footer_labels):
        for label, amount in zip(footer_labels, footer_amounts):
            totals[label] = amount

    return totals


def _resolve_total_key(label: str) -> str | None:
    normalized_label = normalize_label(label)
    for key, values in TOTAL_KEY_ALIASES.items():
        normalized_values = {normalize_label(value) for value in values}
        if normalized_label in normalized_values:
            return key
    return None


def _find_amount_in_row(row: list[str]) -> str | None:
    for cell in row:
        value = str(cell).strip()
        if _looks_like_amount(value):
            return value
    return None


def _looks_like_amount(value: str) -> bool:
    normalized = " ".join(str(value).strip().split())
    if not normalized:
        return False

    return bool(AMOUNT_PATTERN.match(normalized))


def _is_continuation_table(table: dict[str, Any], header_map: dict[str, int]) -> bool:
    rows = table.get("rows") or []
    if not rows:
        return False

    identifier_key = "pos" if "pos" in header_map else "item" if "item" in header_map else None
    identifier_index = header_map.get(identifier_key) if identifier_key else None
    if identifier_index is None:
        return False

    sample_rows = rows[:3]
    for row in sample_rows:
        if identifier_index < len(row):
            cell = str(row[identifier_index]).strip()
            if cell.isdigit():
                return True
    return False


def _is_line_item_row(row: list[str], header_map: dict[str, int]) -> bool:
    identifier_key = "item" if "item" in header_map else "pos" if "pos" in header_map else None
    if identifier_key is None:
        return False

    identifier_index = header_map.get(identifier_key)
    if identifier_index is None or identifier_index >= len(row):
        return False

    identifier = str(row[identifier_index]).strip()
    if not identifier or not any(char.isdigit() for char in identifier):
        return False

    non_empty_cells = [str(cell).strip() for cell in row if str(cell).strip()]
    return len(non_empty_cells) >= 3


def _is_totals_row(row: list[str]) -> bool:
    for cell in row:
        if _resolve_total_key(str(cell)):
            return True
    return False


def _extract_purchase_order_a_table(
    tables: list[dict[str, Any]],
    headers: list[str],
    canonical_columns: list[str],
) -> dict[str, Any]:
    required_main_tokens = [
        normalize_label("Partida Item"),
        normalize_label("No. Requisición"),
        normalize_label("Código (No. de catálogo)"),
        normalize_label("Descripción de los bienes"),
        normalize_label("Texto Corto posición"),
        normalize_label("Cantidad"),
        normalize_label("Unidad"),
        normalize_label("Centro/Alm"),
        normalize_label("Precio unitario Bruto"),
        normalize_label("Valor Bruto"),
    ]

    for table in tables:
        header_parts = []
        for header in table.get("header_fields", []):
            header_parts.append(str(header.get("merged_label") or header.get("content") or ""))
        for header_row in table.get("header_rows", []):
            header_parts.extend(str(cell) for cell in header_row)
        rows = table.get("rows") or []
        for row in rows[:2]:
            header_parts.extend(str(cell) for cell in row)

        header_blob = " ".join(normalize_label(part) for part in header_parts if str(part).strip())
        has_main_header = all(token in header_blob for token in required_main_tokens)
        has_delivery_header = normalize_label("Delivery Date") in header_blob or normalize_label("Programa de entregas") in header_blob
        if not (has_main_header and has_delivery_header):
            continue

        parsed_rows: list[list[str]] = []
        for row in rows:
            cells = [str(cell).strip() for cell in row]
            if not cells or not cells[0].isdigit():
                continue
            if len(cells) < 12:
                continue
            parsed_rows.append(cells[:12])

        if not parsed_rows:
            continue

        normalized_rows = [
            {column_name: row[index] for index, column_name in enumerate(canonical_columns)}
            for row in parsed_rows
        ]
        return {
            "headers": headers,
            "canonical_headers": canonical_columns,
            "rows": parsed_rows,
            "normalized_rows": normalized_rows,
            "source_table_indexes": [table.get("table_index")],
            "page_numbers": table.get("page_numbers", []),
        }

    return {}


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


def _resolve_line_item_header_map(
    table: dict[str, Any],
    canonical_columns: list[str],
    header_aliases: dict[str, set[str]],
) -> dict[str, int]:
    header_candidates = table.get("header_fields") or []
    resolved: dict[str, int] = {}

    for header in header_candidates:
        header_text = str(
            header.get("merged_label")
            or header.get("content")
            or ""
        )
        canonical_name = _match_canonical_header(header_text, canonical_columns, header_aliases)
        column_index = int(header.get("column_index", -1) or -1)
        if canonical_name and canonical_name not in resolved and column_index >= 0:
            resolved[canonical_name] = column_index

    if resolved:
        return resolved

    for column_index, header_text in enumerate((table.get("rows") or [[]])[0] if table.get("rows") else []):
        canonical_name = _match_canonical_header(header_text, canonical_columns, header_aliases)
        if canonical_name and canonical_name not in resolved:
            resolved[canonical_name] = column_index

    return resolved


def _match_canonical_header(
    header_text: str,
    canonical_columns: list[str],
    header_aliases: dict[str, set[str]],
) -> str | None:
    normalized_header = normalize_label(header_text.replace("\n", " "))
    for column_name in canonical_columns:
        aliases = header_aliases.get(column_name, set())
        normalized_aliases = {normalize_label(alias) for alias in aliases}
        if normalized_header in normalized_aliases:
            return column_name
        if any(alias and alias in normalized_header for alias in normalized_aliases):
            return column_name
    return None


def _extract_table_data_rows(table: dict[str, Any]) -> list[list[str]]:
    rows = table.get("rows") or []
    header_row_count = len(table.get("header_rows") or [])
    if header_row_count > 0:
        return rows[header_row_count:]
    return rows[1:] if len(rows) > 1 else []
