from __future__ import annotations

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
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


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
